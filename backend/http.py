""" API 통신에 반복적으로 필요한 로직 모듈화 """
import asyncio
from typing import List

import jwt
import httpx
import wbdata
from aiocache import cached
from fastapi import HTTPException, Request, APIRouter, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from backend.system import SECRETS, log, run_async


class CognitoToken:
    """AWS Cognito token auth"""

    jwks = {"keys": []}

    def __init__(self, id_token, access_token):
        self.id_token = id_token
        self.access_token = access_token

    async def get_jwk(self, key_id: str):
        matching = [item for item in self.jwks["keys"] if item["kid"] == key_id]
        if not matching:  # Cognito에서 키 jwks가 변경(롤오버)되었다고 간주하고 업데이트 후 재시도
            log.warning(f"매칭되는 JWK가 없습니다. Cognito로부터 jwks를 업데이트합니다.")
            async with httpx.AsyncClient(
                base_url="https://cognito-idp.us-east-1.amazonaws.com/"
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
        return {"id": access_info["username"], "email": id_info["email"]}


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


class Router:
    auth = CognitoTokenBearer()

    def __init__(self, tag: str):
        self.public = APIRouter(prefix="/api", tags=[tag])
        self.private = APIRouter(
            prefix="/api", tags=[tag], dependencies=[Depends(self.auth)]
        )
        self.private.user = Depends(self.auth)


class FmpAPI:
    """financialmodelingprep API GET Request"""

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
