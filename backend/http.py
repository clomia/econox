""" API 통신에 반복적으로 필요한 로직 모듈화 """
import json
import time
import base64
import asyncio
from uuid import uuid4
from typing import List, Awaitable, Callable, TypeVar
from functools import partial

import jwt
import httpx
import wbdata
from aiocache import cached
from fastapi import routing, HTTPException, Request, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.system import SECRETS, log, run_async

T = TypeVar("T")


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
            log.warning(f"매칭되는 JWK가 없습니다. Cognito로부터 jwks를 업데이트합니다.")
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
            options={"verify_signature": True, "verify_aud": True},
        )
        access_info = jwt.decode(
            self.access_token,
            key=jwt.algorithms.RSAAlgorithm.from_jwk(
                await self.get_jwk(jwt.get_unverified_header(self.access_token)["kid"])
            ),
            algorithms=["RS256"],
            options={"verify_signature": True, "verify_aud": False},
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
        credentials: HTTPAuthorizationCredentials = await super().__call__(request)

        if "|" not in credentials.credentials:
            raise HTTPException(status_code=403, detail="Invalid token format")
        id_token, access_token = credentials.credentials.split("|")

        if not id_token or not access_token:
            raise HTTPException(status_code=403, detail="Not authenticated")

        token = CognitoToken(id_token, access_token)
        try:
            user_info = await token.authentication()
            return user_info
        except jwt.PyJWTError as e:
            e_str = str(e)
            error_detail = e_str[0].lower() + e_str[1:]
            raise HTTPException(status_code=403, detail=f"Authorization {error_detail}")


class APIRouter:
    auth = CognitoTokenBearer()

    def __init__(self, prefix: str):
        self.path = f"/api/{prefix}"
        self.public = routing.APIRouter(prefix=self.path, tags=[prefix])
        self.private = routing.APIRouter(
            prefix=self.path, tags=[prefix], dependencies=[Depends(self.auth)]
        )
        self.private.auth = Depends(self.auth)

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
        for interval in [0, 0.2, 0.5, 1, 2, 3, 5, 6, None]:
            try:
                return await request(path, **params)
            except Exception as error:
                log.warning(
                    "FMP API 서버와 통신에 실패했습니다."
                    f"{interval}초 후 다시 시도합니다... (path: {path})"
                )
                if interval is None:
                    log.error(f"FMP API 서버와 통신에 실패하여 데이터를 수신하지 못했습니다. (path: {path})")
                    raise error  # 끝까지 통신에 실패하면 에러
                else:
                    await asyncio.sleep(interval)  # retry 대기
                    continue

    async def _request(cls, path, **params):
        async with httpx.AsyncClient(
            base_url="https://financialmodelingprep.com",
            params={"apikey": SECRETS["FMP_API_KEY"]},
            timeout=cls.timeout,
        ) as fmp_client:
            resp = await fmp_client.get(path, params=params)
            resp.raise_for_status()
        return resp.json()

    @classmethod
    @cached(ttl=12 * 360)
    async def _request_use_caching(cls, path, **params):
        return await cls._request(path, **params)


class WorldBankAPI:
    """World Bank Open API Request"""

    @classmethod
    @cached(ttl=12 * 360)
    async def get_data(cls, indicator, country) -> List[dict]:
        """국가의 지표 시계열을 반환합니다."""
        result = await run_async(cls._safe_caller(wbdata.get_data), indicator, country)
        return result if result else []

    @classmethod
    @cached(ttl=12 * 360)
    async def get_indicator(cls, indicator) -> dict:
        """지표에 대한 상세 정보를 반환합니다. 정보가 없는 경우 빈 딕셔너리가 반환됩니다."""
        result = await run_async(cls._safe_caller(wbdata.get_indicator), indicator)
        return result[0] if result else {}

    @classmethod
    @cached(ttl=12 * 360)
    async def search_countries(cls, text) -> List[dict]:
        """자연어로 국가들을 검색합니다."""
        result = await run_async(cls._safe_caller(wbdata.search_countries), text)
        return list(result) if result else []

    @classmethod
    @cached(ttl=12 * 360)
    async def get_country(cls, code) -> dict:
        """국가 코드에 해당하는 국가를 반환합니다.."""
        result = await run_async(cls._safe_caller(wbdata.get_country), code)
        return result[0] if result else {}

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
        return resp.json()

    @classmethod
    async def create_billing(
        cls,
        cognito_user_id: str,
        card_number: str,
        expiration_year: str,
        expiration_month: str,
        owner_id: str,
        email: str,
        order_name: str,
        amount: int,
    ) -> dict:
        """
        - 빌링키를 발급받고 카드 정보로 대금을 결제합니다
        - return: 빌링키와 결제정보
            - 빌링키 이미 있으면 billing 메서드를 통해 빌링키로 결제하세요
        """
        # -- 빌링 키 발급 --
        try:
            billing_info = await cls("/v1/billing/authorizations/card").post(
                {
                    "customerKey": cognito_user_id,
                    "cardNumber": card_number,
                    "cardExpirationYear": expiration_year,
                    "cardExpirationMonth": expiration_month,
                    "customerIdentityNumber": owner_id,
                }
            )
            # -- 첫달 구독료 결제 --
            billing_key = billing_info["billingKey"]
            payment_info = await cls.billing(
                billing_key, cognito_user_id, order_name, amount, email
            )
        except httpx.HTTPStatusError as e:
            raise HTTPException(
                status_code=402,
                detail=f"The Tosspayments information provided is incorrect\nResponse detail: {e}",
            )
        return {"key": billing_key, "payment": payment_info}

    @classmethod
    async def billing(
        cls, key: str, cognito_user_id: str, order_name: str, amount: int, email: str
    ):
        """
        - 빌링 키로 대금을 결제합니다
        - key: tosspayments billingKey
        - return: POST /v1/billing/{billingKey} 요청에 대한 응답
        """
        return await cls(f"/v1/billing/{key}").post(
            {
                "customerKey": cognito_user_id,
                "orderId": str(uuid4()),
                "orderName": order_name,
                "amount": amount,
                "customerEmail": email,
            }
        )


class PayPalAPI:
    """PayPal에 HTTP 요청을 보냅니다."""

    timeout = 30
    host = "https://api.sandbox.paypal.com"
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
        if resp.status_code != 200:
            log.error(f"PayPal Access Token 발급에 실패했습니다.\n응답:{resp.json()}")
        resp.raise_for_status()
        cls.access_token = resp.json()["access_token"]

    @classmethod
    async def _webhook_verifier(cls, event_type: str, event: Request = None):
        body = await event.json()
        webhook_id = json.loads(SECRETS["PAYPAL_WEBHOOK_ID"])
        try:
            result = await cls("/v1/notifications/verify-webhook-signature").post(
                {
                    "auth_algo": event.headers["paypal-auth-algo"],
                    "cert_url": event.headers["paypal-cert-url"],
                    "transmission_id": event.headers["paypal-transmission-id"],
                    "transmission_sig": event.headers["paypal-transmission-sig"],
                    "transmission_time": event.headers["paypal-transmission-time"],
                    "webhook_id": webhook_id[event_type],
                    "webhook_event": body,
                }
            )
            assert result["verification_status"] == "SUCCESS"
        except (httpx.HTTPStatusError, AssertionError, KeyError) as e:
            log.warning(
                f"PayPal 웹훅 페이로드 인증 실패, 요청을 무시합니다."
                f"\n[Header]:{dict(event.headers)}\n[Body]: {body}\n[Error] {type(e).__name__}: {e}"
            )
            raise HTTPException(status_code=401, detail="Event verification failed")

    @classmethod
    def webhook_verifier(cls, event_type: str):
        """
        - 웹훅 이벤트 타입 문자열을 받아서 해당 이벤트를 검증하는 의존성 함수를 반환합니다.
        - secrets_manager에 PAYPAL_WEBHOOK_ID 키로 JSON 형식의 웹훅 ID 정의가 있어야 합니다.
        """
        return partial(cls._webhook_verifier, event_type)

    async def _execute_request(self, request: Awaitable, retry: Awaitable[dict | list]):
        """API 요청을 실행하고 토큰을 갱신하는 부분을 캡슐화"""
        try:
            resp = await request
        except httpx.LocalProtocolError as e:
            log.warning(  # resp는 undifined임, 토큰 없으면 요청 자체가 실행되지 않음
                f"POST {self.path} -> {e}\nPayPal 토큰 인증에 실패하였습니다. 토큰 갱신 후 재시도합니다."
            )
            await self._refresh_access_token()
            return await retry()
        resp.raise_for_status()
        return resp.json()

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


async def pooling(
    target: Awaitable[T],
    inspecter: Callable[[T], bool] = lambda _: True,
    exceptions: tuple | Exception = tuple(),
    timeout: int = 15,
):
    """
    - 조건을 만족하는 반환값이 나올때까지 함수를 재실행합니다.
    - target: 무결성이 보장되어야 하는 대상 함수 (Async I/O Bound Function)
    - inspecter: target함수의 반환값을 검사하는 함수 - bool을 반환해야 함
    - exceptions: target 함수에서 발생될 예외중 무시할 예외들
    - timeout: 재시도 시간제한(초)
        - timeout 초과시 AssertionError가 발생합니다.
    - 비동기 함수를 대상으로 하는 비동기 함수이므로 await 빼먹지 않도록 주의
    """
    start = time.time()
    while time.time() < start + timeout:
        try:
            if inspecter(result := await target()):
                return result
        except exceptions:
            continue
    assert inspecter(result := await target())
    return result
