""" 외부 리소스 (클라우드 서비스, 데이터 API 등)에 대한 비동기 통신 클라이언트 객체들 """
import re
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
from aiocache import cached
from fastapi import routing, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend import db
from backend.math import utcstr2datetime
from backend.system import SECRETS, log

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

        exponential_delay = base_delay * ((1.5**retry) - 1)  # 지수 백오프
        random_max = 5.6 * delay_limit
        random_factor = random.uniform(0.1, random_max)  # 무작위성 추가
        random_delay = random_factor * exponential_delay
        delay = min(random_delay, delay_limit)
        # 무작위성을 많이 넣어야 동시에 많이 실행될 때 호출 시간 분포가 잘 흩어진다.
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
    - 기본적인 코드니토 토큰 검증을 구현합니다.
    - 이 토큰은 Cognito idToken과 accessToken을 '|'로 이어붙인것입니다.
    - 두 토큰을 검증한 뒤 유저정보(id, email)를 제공합니다.
    """

    async def __call__(self, request: Request) -> dict:
        """토큰을 검증하고 해당하는 유저 정보를 반환합니다."""
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
            if not (db_user := await db.get_user(user_id=user_info["id"])):
                raise HTTPException(
                    status_code=401,
                    detail=f"Authorization failed, user does not exists",
                )
            user = user_info | db_user
            user["id"] = str(user["id"])  # UUID -> str (UUID 타입 쓸모 없음 코드 복잡도만 늘어남)
            return user
        except jwt.PyJWTError as e:
            e_str = str(e)
            error_detail = e_str[0].lower() + e_str[1:]
            raise HTTPException(status_code=401, detail=f"Authorization {error_detail}")


class ServiceTokenBearer(CognitoTokenBearer):
    """
    - 코그니토 토큰을 기반으로 맴버십에 따른 권한까지 검증합니다.
    - 대금이 밀려 청구 상태가 "require"인 경우 402 응답.
    - 요구되는 맴버십과 맞지 않는 유저인 경우 403 응답.
    """

    def __init__(self, authority: Literal["all", "basic", "professional"]):
        super().__init__()
        self.authority = authority

    async def __call__(self, request: Request) -> dict:
        db_user = await super().__call__(request)
        match self.authority:
            case "all":  # 서비스 회원 모두 허용
                return db_user
            case "basic":  # 맴버십이 basic 이상인 회원만 허용
                if db_user["billing_status"] == "require":
                    raise HTTPException(
                        status_code=402,
                        detail="This account has unpaid membership fees. Payment is required",
                    )
                return db_user
            case "professional":  # 맴버십이 professional 이상인 회원만 허용
                if db_user["billing_status"] == "require":
                    raise HTTPException(
                        status_code=402,
                        detail="This account has unpaid membership fees. Payment is required",
                    )
                if db_user["membership"] != "professional":
                    raise HTTPException(
                        status_code=403,
                        detail="Professional membership is required. Your membership is basic",
                    )
                return db_user


class APIRouter:
    """
    - 권한 계층별로 라우터 객체를 제공함
    - public: 아무나 요청 가능
    - private: 로그인된 유저만 요청 가능
    - basic: private + 구독 비용을 지불한 유저만 요청 가능
    - professional: basic + professional맴버십 유저만 요청 가능
    """

    allow_all_user = Depends(ServiceTokenBearer("all"))
    allow_basic_user = Depends(ServiceTokenBearer("basic"))
    allow_professional_user = Depends(ServiceTokenBearer("professional"))

    def __init__(self, prefix: str):
        self.path = f"/api/{prefix}"
        self.public = routing.APIRouter(prefix=self.path, tags=[prefix])
        self.private = routing.APIRouter(
            prefix=self.path, tags=[prefix], dependencies=[self.allow_all_user]
        )
        self.basic = routing.APIRouter(
            prefix=self.path,
            tags=[prefix],
            dependencies=[self.allow_basic_user],
        )
        self.professional = routing.APIRouter(
            prefix=self.path,
            tags=[prefix],
            dependencies=[self.allow_professional_user],
        )

        # 각 라우터에 대해서 유저 정보애 접근할 수 있도록 Depends 객체를 속성으로 할당
        # Depends는 한번의 API호출에 대해서 한번만 실행되므로 쿼리 반복 실행 등에 대한 걱정 안해도 됌
        # 여기에서는 API 함수가 어떤 라우터를 사용했는지 알 방법이 없으므로 이렇게 제공하는수밖에 없음..
        # 따라서  API 함수가 사용한 라우터에 맞게 알아서 가져다 써야 함
        # user 값은 db.get_user 가 반환한 dict임
        self.private.user = self.allow_all_user
        self.basic.user = self.allow_basic_user
        self.professional.user = self.allow_professional_user

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
            return await pooling(
                partial(request, path, **params), exceptions=Exception, timeout=20
            )
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
    """

    BASE_URL = "http://api.worldbank.org/v2"
    countries = None

    async def pagenation_api_call(self, endpoint: str, params: dict = {}) -> list:
        """pagenation을 통해 모든 배열 응답을 모아서 반환합니다."""
        timeout = 20
        all_data = []
        page = 0
        start = time.time()

        async with httpx.AsyncClient() as client:
            params["format"] = "json"
            params["per_page"] = 1000
            while True:
                page += 1
                params["page"] = page

                async def request():
                    resp = await client.get(
                        f"{self.BASE_URL}/{endpoint}",
                        params=params,
                    )
                    resp.raise_for_status()
                    return resp

                resp = await pooling(request, exceptions=Exception)
                if len(resp.json()) != 2:
                    break  # [{'message': [{'id': '120', 'key': 'Invalid value', 'value': 'The provided parameter value is not valid'}]}]
                meta, data = resp.json()
                all_data.extend(data)
                if meta["page"] == meta["pages"]:
                    break  # 현재 페이지가 총 페이지 갯수와 같다면 종료
                if time.time() - start > timeout:
                    log.error(
                        f"[WorldBankAPI.pagenation_api_call 시간초과로 데이터 수집 중단 Timeout=({timeout}초)] "
                        f"[Endpoint={endpoint}, Params={params}] 마지막으로 수집한 페이지: {page}, 현재까지 수집된 데이터: {all_data}"
                    )
                    break
        return all_data

    async def api_call(self, endpoint: str, params: dict = {}) -> dict | list:
        """단순히  API 요청 후 응답 반환"""
        params["format"] = "json"
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"{self.BASE_URL}/{endpoint}", params=params)
            resp.raise_for_status()
            return resp.json()

    @cached(ttl=12 * 360)  # 이건 상위 객체에서 zarr 파일로 캐싱됨
    async def get_data(self, indicator: str, country: str) -> list:
        data = await self.pagenation_api_call(
            f"country/{country}/indicator/{indicator}"
        )
        return data

    @cached()  # 메타정보는 영구 캐싱
    async def get_indicator(self, indicator: str) -> dict:
        request = partial(self.api_call, f"indicator/{indicator}")
        try:
            return (await pooling(request, exceptions=Exception))[1][0]
        except IndexError:
            return {}

    # self.countries 속성을 통해 API 호출을 캐싱하므로 별도의 캐싱 불필요
    async def search_countries(self, query: str) -> list:
        if not self.countries:
            self.countries = await self.pagenation_api_call("countries")
        pattern = re.compile(query, re.IGNORECASE)
        return [
            country for country in self.countries if pattern.search(country["name"])
        ]

    @cached()  # 메타정보는 영구 캐싱
    async def get_country(self, code: str) -> dict:
        request = partial(self.api_call, f"country/{code}")
        try:
            return (await pooling(request, exceptions=Exception))[1][0]
        except IndexError:
            return {}


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
                f"POST {self.path}: PayPal 토큰 인증에 실패하였습니다. 토큰 갱신 후 재시도합니다. ({e})"
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
