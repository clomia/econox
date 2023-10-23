""" 외부 리소스 (클라우드 서비스, 데이터 API 등)에 대한 비동기 통신 클라이언트 객체들 """
import json
import time
import random
import base64
import asyncio
from uuid import uuid4
from datetime import datetime
from typing import List, Awaitable, Callable, TypeVar, Literal
from functools import partial

import jwt
import httpx
import wbdata
from aiocache import cached
from fastapi import routing, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend import db
from backend.math import utcstr2datetime
from backend.system import SECRETS, log, run_async

T = TypeVar("T")


async def pooling(
    target: Awaitable[T],
    inspecter: Callable[[T], bool] = lambda _: True,
    exceptions: tuple | Exception = tuple(),
    timeout: int = 15,
    exponential_backoff=True,
):
    """
    - 조건을 만족하는 반환값이 나올때까지 함수를 재실행합니다.
    - target: 무결성이 보장되어야 하는 대상 함수 (Async I/O Bound Function)
    - inspecter: target함수의 반환값을 검사하는 함수, bool을 반환해야 함
    - exceptions: target 함수에서 발생될 예외중 무시할 예외들
    - timeout: 재시도 시간제한(초)
        - inspecter가 있는 경우 timeout 초과시 AssertionError가 발생합니다.
        - exceptions가 있는 경우 timeout 초과시 exceptions를 무시하지 않고 raise합니다.
    - exponential_backoff: 지수 백오프로 점진적인 대기 수행 여부 [Default: True]
        - False로 설정 시 함수를 즉각 재시도함
    - 비동기 함수를 대상으로 하는 비동기 함수이므로 await 빼먹지 않도록 주의
    """
    retry = -1
    base_delay = 0.05
    delay_limit = 7  # base_delay 0.05에서 시작해서 8번 재시도하면 약 6.45초 도달

    start = time.time()
    while time.time() < start + timeout:
        retry += 1
        try:
            if inspecter(result := await target()):  # 함수 실행
                return result
        except exceptions:
            pass
        if not exponential_backoff:  # 재수 백오프 비활성화시 바로 재시도
            continue

        exponential_delay = base_delay * (2**retry)  # 지수 백오프
        random_delay = random.uniform(0, 0.1 * exponential_delay)  # 무작위성 추가
        # delay_limit을 넘지 못하도록
        delay = min(exponential_delay + random_delay, delay_limit)
        await asyncio.sleep(delay)

    assert inspecter(result := await target())  # 마지막으로 한번 더 실행
    return result


class CognitoToken:
    """AWS Cognito token auth"""

    timeout = 15
    jwks = {"keys": []}

    def __init__(self, id_token: str, access_token: str):
        self.id_token = id_token
        self.access_token = access_token

    async def get_jwk(self, key_id: str):
        matching = [item for item in self.jwks["keys"] if item["kid"] == key_id]
        if not matching:  # Cognito에서 키 jwks가 변경(롤오버)되었다고 간주하고 업데이트 후 재시도
            log.info(f"매칭되는 JWK가 없습니다. Cognito로부터 jwks를 업데이트합니다.")
            async with httpx.AsyncClient(
                base_url="https://cognito-idp.us-east-1.amazonaws.com/",
                timeout=self.timeout,
            ) as client:
                self.__class__.jwks = (
                    await client.get(
                        f"{SECRETS['COGNITO_USER_POOL_ID']}/.well-known/jwks.json"
                    )
                ).json()
            return await self.get_jwk(key_id)
        return matching[0]

    async def authentication(self):
        """id token과 access token의 서명을 검증하고 디코딩해서 유저 id와 이메일을 반환합니다."""
        id_info = jwt.decode(
            self.id_token,
            key=jwt.algorithms.RSAAlgorithm.from_jwk(
                await self.get_jwk(jwt.get_unverified_header(self.id_token)["kid"])
            ),
            algorithms=["RS256"],
            audience=SECRETS["COGNITO_APP_CLIENT_ID"],
            options={
                "verify_signature": True,
                "verify_aud": True,
                "verify_iat": False,  # 토큰 발행 시간 검증 비활성화 (개발환경, 인증서버간 시차때문에)
            },
        )
        access_info = jwt.decode(
            self.access_token,
            key=jwt.algorithms.RSAAlgorithm.from_jwk(
                await self.get_jwk(jwt.get_unverified_header(self.access_token)["kid"])
            ),
            algorithms=["RS256"],
            options={
                "verify_signature": True,
                "verify_aud": False,
                "verify_iat": False,
            },
        )
        return {
            "id": access_info["username"],
            "email": id_info["email"],
            "cognito_id_token": self.id_token,
            "cognito_access_token": self.access_token,
        }


class CognitoTokenBearer(HTTPBearer):
    """
    - 이 토큰은 Cognito idToken과 accessToken을 '|'로 이어붙인것입니다.
    - 두 토큰을 검증한 뒤 유저정보(id, email)를 제공합니다.
    """

    async def __call__(self, request: Request) -> dict:
        try:
            credentials: HTTPAuthorizationCredentials = await super().__call__(request)
        except HTTPException:
            # HTTPBearer는 Not authenticated에 대해 403을 응답하지만 우리는 그것에 401을 쓸거임
            raise HTTPException(status_code=401, detail="Not authenticated")

        if "|" not in credentials.credentials:
            raise HTTPException(status_code=401, detail="Invalid token format")
        id_token, access_token = credentials.credentials.split("|")

        if not id_token or not access_token:
            raise HTTPException(status_code=401, detail="Not authenticated")

        token = CognitoToken(id_token, access_token)
        try:
            user_info = await token.authentication()
            user = await db.select_row(
                "users",
                fields=["membership", "billing_status"],
                where={"id": user_info["id"]},
            )
            if not user:
                raise HTTPException(
                    status_code=401,
                    detail=f"Authorization failed, user does not exists",
                )
            user_info |= {  # user_info에 맴버십과 청구상태 추가
                "membership": user["membership"],
                "billing_status": user["billing_status"],
            }  # 유저 존재 확인 겸, MembershipPermissionInspector에서 필요로 하는 정보 미리 삽입
        except jwt.PyJWTError as e:
            e_str = str(e)
            error_detail = e_str[0].lower() + e_str[1:]
            raise HTTPException(status_code=401, detail=f"Authorization {error_detail}")
        else:
            return user_info


class MembershipPermissionInspector(CognitoTokenBearer):
    """
    - 맴버십 API 권한 의존성
    - 대금이 밀려 청구 상태가 "require"인 경우 402 응답.
    - 요구되는 맴버십과 맞지 않는 유저인 경우 403 응답.
    """

    def __init__(self, membership: Literal["basic", "professional"]):
        super().__init__()
        self.membership = membership

    async def __call__(self, request: Request) -> dict:
        user_info = await super().__call__(request)
        if user_info["billing_status"] == "require":
            raise HTTPException(
                status_code=402,
                detail="This account has unpaid membership fees. Payment is required",
            )
        elif self.membership == "professional" and user_info["membership"] == "basic":
            raise HTTPException(
                status_code=403,
                detail="Professional membership is required. Your membership is basic",
            )
        return user_info


class APIRouter:
    """
    - 권한 계층별로 라우터 객체를 제공함
    - public: 아무나 요청 가능
    - private: 로그인된 유저만 요청 가능
    - basic: private + 구독 비용을 지불한 유저만 요청 가능
    - professional: basic + professional맴버십 유저만 요청 가능
    """

    auth = Depends(CognitoTokenBearer())
    permission = {
        "basic": Depends(MembershipPermissionInspector("basic")),
        "professional": Depends(MembershipPermissionInspector("professional")),
    }

    def __init__(self, prefix: str):
        self.path = f"/api/{prefix}"
        self.public = routing.APIRouter(prefix=self.path, tags=[prefix])
        self.private = routing.APIRouter(
            prefix=self.path, tags=[prefix], dependencies=[self.auth]
        )
        self.basic = routing.APIRouter(
            prefix=self.path,
            tags=[prefix],
            dependencies=[self.permission["basic"]],
        )
        self.professional = routing.APIRouter(
            prefix=self.path,
            tags=[prefix],
            dependencies=[self.permission["professional"]],
        )

        self.private.auth = self.auth
        self.basic.auth = self.permission["basic"]
        self.professional.auth = self.permission["professional"]

        # fastapi.APIRouter의 메서드가 path 인자를 입력받지 않은 경우 기본값 "" 를 사용하도록 변경
        methods = ["get", "post", "put", "patch", "delete", "options", "head", "trace"]
        for method in methods:
            target = getattr(self.public, method)
            setattr(self.public, method, self.method_wrapping(target))

            target = getattr(self.private, method)
            setattr(self.private, method, self.method_wrapping(target))

    @staticmethod
    def method_wrapping(func):
        def wrapper(path="", *args, **kwargs):
            return func(path, *args, **kwargs)

        return wrapper


class FmpAPI:
    """financialmodelingprep API GET Request"""

    timeout = 600

    def __init__(self, cache: bool):
        self.cache = cache

    async def get(self, path, **params) -> dict | list:
        request = self._request_use_caching if self.cache else self._request
        try:
            return await pooling(partial(request, path, **params), exceptions=Exception)
        except Exception as e:
            log.error(
                f"FMP API 서버와 통신에 실패하여 데이터를 수신하지 못했습니다. (path: {path}, error: {e})"
            )

    @classmethod
    async def _request(cls, path, **params):
        async with httpx.AsyncClient(
            base_url="https://financialmodelingprep.com",
            params={"apikey": SECRETS["FMP_API_KEY"]},
            timeout=cls.timeout,
        ) as fmp_client:
            resp = await fmp_client.get(path, params=params)
            resp.raise_for_status()
        return resp.json() if resp.content else {}

    @classmethod
    @cached(ttl=12 * 360)
    async def _request_use_caching(cls, path, **params):
        return await cls._request(path, **params)


class WorldBankAPI:
    """
    - World Bank Open API Request
    - wbdata SDK의 각 함수에 캐싱, 비동기 호출, 지수 백오프 풀링 로직을 첨가하여 제공
    """

    @classmethod
    @cached(ttl=12 * 360)
    async def get_data(cls, indicator, country) -> List[dict]:
        """국가의 지표 시계열을 반환합니다."""
        result = await cls._exec(wbdata.get_data, indicator, country)
        return result if result else []

    @classmethod
    @cached(ttl=12 * 360)
    async def get_indicator(cls, indicator) -> dict:
        """지표에 대한 상세 정보를 반환합니다. 정보가 없는 경우 빈 딕셔너리가 반환됩니다."""
        result = await cls._exec(wbdata.get_indicator, indicator)
        return result[0] if result else {}

    @classmethod
    @cached(ttl=12 * 360)
    async def search_countries(cls, text) -> List[dict]:
        """자연어로 국가들을 검색합니다."""
        result = await cls._exec(wbdata.search_countries, text)
        return list(result) if result else []

    @classmethod
    @cached(ttl=12 * 360)
    async def get_country(cls, code) -> dict:
        """국가 코드에 해당하는 국가를 반환합니다.."""
        result = await cls._exec(wbdata.get_country, code)
        return result[0] if result else {}

    @classmethod
    async def _exec(cls, wb_func, *args):
        try:
            return await pooling(
                partial(run_async, cls._safe_caller(wb_func), *args),
                exceptions=Exception,
            )
        except Exception as e:
            log.error(
                f"World Bank API 서버와 통신에 실패하여 데이터를 수신하지 못했습니다."
                f"(wbdata func: {wb_func.__name__}, args: {args}, error: {e})"
            )

    @staticmethod
    def _safe_caller(wb_func):
        """
        - wbdata 함수가 안전하게 작동하도록 감쌉니다.
        - wbdata 라이브러리의 캐싱 알고리즘은 thread-safe하지 않으므로
        항상 cache=False 해줘야 하며, 결과가 없을 때 RuntimeError를 발생시키는데
        에러를 발생시키는 대신에 None을 반환하도록 변경합니다.
        """

        def wrapper(*args, **kwargs):
            try:
                return wb_func(*args, **kwargs, cache=False)
            except RuntimeError:
                return None

        return wrapper


class TosspaymentsAPI:
    """tosspayments에 HTTP 요청을 보냅니다."""

    timeout = 30
    host = "https://api.tosspayments.com"
    token = base64.b64encode(
        (SECRETS["TOSSPAYMENTS_SECRET_KEY"] + ":").encode("utf-8")
    ).decode("utf-8")

    def __init__(self, path):
        """path: API 경로 (예시: "/v1/billing/authorizations/card")"""
        self.path = path

    async def post(self, payload: dict) -> dict | list:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            resp = await client.post(
                self.host + self.path,
                headers={
                    "Authorization": f"Basic {self.token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
        resp.raise_for_status()
        return resp.json() if resp.content else {}


class TosspaymentsBilling:
    def __init__(self, user_id):
        self.user_id = user_id

    async def get_billing_key(
        self,
        card_number: str,
        expiration_year: str,
        expiration_month: str,
        owner_id: str,
    ) -> str:
        billing_info = await TosspaymentsAPI("/v1/billing/authorizations/card").post(
            {
                "customerKey": self.user_id,
                "cardNumber": card_number,
                "cardExpirationYear": expiration_year,
                "cardExpirationMonth": expiration_month,
                "customerIdentityNumber": owner_id,
            }
        )
        return billing_info["billingKey"]

    async def billing(
        self, key: str, order_name: str, amount: int, email: str | None = None
    ) -> dict:
        """
        - 빌링 키로 대금을 결제합니다
        - key: tosspayments billingKey
        - return: POST /v1/billing/{billingKey} 요청에 대한 응답
        """
        payment_info = await TosspaymentsAPI(f"/v1/billing/{key}").post(
            {
                "amount": str(amount),
                "customerKey": self.user_id,
                "orderId": str(uuid4()),
                "orderName": order_name,
                "customerEmail": email,
            }
        )
        return payment_info


class PayPalAPI:
    """PayPal에 HTTP 요청을 보냅니다."""

    timeout = 30
    host = "https://api.sandbox.paypal.com"  # * 샌드박스랑 프로덕션 host 주소가 다르다
    token = base64.b64encode(
        f"{SECRETS['PAYPAL_CLIENT_ID']}:{SECRETS['PAYPAL_SECRET_KEY']}".encode("utf-8")
    ).decode("utf-8")
    access_token = ""  # 첫 요청 시 받아옴

    def __init__(self, path: str) -> None:
        """path: API 경로 (예시: "/v2/customer/partner-referrals")"""
        self.path = path

    @classmethod
    async def _refresh_access_token(cls):
        async with httpx.AsyncClient(timeout=cls.timeout) as client:
            resp = await client.post(
                f"{cls.host}/v1/oauth2/token",
                headers={
                    "Authorization": f"basic {cls.token}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                data={"grant_type": "client_credentials"},
            )
        if resp.status_code != 200 and resp.content:
            log.error(f"PayPal Access Token 발급에 실패했습니다.\n응답:{resp.json()}")
        resp.raise_for_status()
        cls.access_token = resp.json()["access_token"]

    async def _execute_request(self, request: Awaitable, retry: Awaitable[dict | list]):
        """API 요청을 실행하고 토큰을 갱신하는 부분을 캡슐화"""
        try:
            resp = await request
            if resp.status_code == 401:  # 토큰이 만료됨 (만약 다른곳에서 토큰 발급시 이전 토큰이 만료됨)
                raise httpx.LocalProtocolError(message=f"Received 401: {resp.content}")
        except httpx.LocalProtocolError as e:
            # 토큰이 없는 경우는 LocalProtocolError가 바로 raise 됨
            log.info(  # resp는 undifined임, 토큰 없으면 요청 자체가 실행되지 않음
                f"POST {self.path}: PayPal 토큰 인증에 실패하였습니다. 토큰 갱신 후 재시도합니다. (error message: {e})"
            )
            await self._refresh_access_token()
            return await retry()
        resp.raise_for_status()
        return resp.json() if resp.content else {}

    async def post(self, payload: dict = {}) -> dict | list:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            request = client.post(
                self.host + self.path,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                json=payload,
            )
            return await self._execute_request(
                request, retry=partial(self.post, payload)
            )

    async def get(self, params: dict = {}) -> dict | list:
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            request = client.get(
                self.host + self.path,
                headers={
                    "Authorization": f"Bearer {self.access_token}",
                    "Content-Type": "application/json",
                },
                params=params,
            )
            return await self._execute_request(request, retry=partial(self.get, params))


async def get_paypal_next_billing_date(subscription_id: str) -> datetime:
    """구독의 유효성을 검증하고 다음 결제 날짜를 반환합니다. 유효하지 않은 경우 AssertionError"""
    target_api = f"/v1/billing/subscriptions/{subscription_id}"
    subscription = await pooling(
        target=PayPalAPI(target_api).get,
        inspecter=lambda results: results["status"] == "ACTIVE",
        timeout=30,
    )
    return utcstr2datetime(subscription["billing_info"]["next_billing_time"])


class PayPalWebhookAuth:
    def __init__(self, event_type: str):
        self.event_type = event_type

    async def __call__(self, event: Request = None):
        """
        - secrets_manager에 PAYPAL_WEBHOOK_ID 키로 JSON 형식의 웹훅 ID 정의가 있어야 합니다.
        """

        body = await event.json()
        webhook_id = json.loads(SECRETS["PAYPAL_WEBHOOK_ID"])
        try:
            result = await PayPalAPI("/v1/notifications/verify-webhook-signature").post(
                {
                    "auth_algo": event.headers["paypal-auth-algo"],
                    "cert_url": event.headers["paypal-cert-url"],
                    "transmission_id": event.headers["paypal-transmission-id"],
                    "transmission_sig": event.headers["paypal-transmission-sig"],
                    "transmission_time": event.headers["paypal-transmission-time"],
                    "webhook_id": webhook_id[self.event_type],
                    "webhook_event": body,
                }
            )
            assert result["verification_status"] == "SUCCESS"
        except (httpx.HTTPStatusError, AssertionError, KeyError) as e:
            log.info(
                f"PayPal 웹훅 페이로드 인증 실패, 요청을 무시합니다."
                f"\n[Header]:{dict(event.headers)}\n[Body]: {body}\n[Error] {type(e).__name__}: {e}"
            )
            raise HTTPException(status_code=401, detail="Event verification failed")


@cached(ttl=10 * 24 * 360)  # 번역 비용 비싸서 오래 캐싱
async def deepl_translate(text: str, to_lang: str, *, from_lang: str = None) -> str:
    """deepl 공식 SDK쓰면 urllib 풀 사이즈 10개 제한 떠서 httpx 비동기 클라이언트로 별도의 함수 작성"""

    host = "https://api-free.deepl.com/v2/translate"  # * 유료버전이랑 무료버전 host 주소가 다르다
    variant_hendler = {
        "en": "EN-US",
        "pt": "PT-PT",
    }  # https://www.deepl.com/docs-api/translate-text/?utm_source=github&utm_medium=github-python-readme (Request Parameters부분의 source_lang, target_lang 섹션 참조)

    target_language = to_lang.upper()
    if to_lang in variant_hendler:
        target_language = variant_hendler[to_lang]
    source_language = from_lang.upper() if from_lang else None

    async def request():
        async with httpx.AsyncClient(timeout=18) as client:
            return await client.post(
                host,
                headers={
                    "Authorization": f"DeepL-Auth-Key {SECRETS['DEEPL_API_KEY']}",
                    "Content-Type": "application/json",
                },
                json={
                    "text": [text],
                    "target_lang": target_language,
                    "source_lang": source_language,
                },
            )

    try:
        resp = await pooling(
            request,  # https://www.deepl.com/ko/docs-api/api-access/error-handling
            inspecter=lambda resp: resp.status_code == 200,
            exceptions=Exception,
        )
    except (AssertionError, Exception) as e:
        raise httpx.HTTPError(f"DeepL 통신 오류 Error: {e}")
    else:
        return resp.json()["translations"][0]["text"]
