""" API 통신에 반복적으로 필요한 로직 모듈화 """
import asyncio
from typing import List

import httpx
import wbdata
from aiocache import cached

from backend.system import SECRETS, log, run_async


class CognitoToken:
    def __init__(self, id_token, access_token):
        self.id_token = id_token
        self.access_token = access_token

    # 캐싱이 아니라 키 롤오버된걸로 판단되면 다시 가져오는 로직으로 해야 함, 캐싱은 잘못된 솔루션임!!
    async def get_jwks(cls):
        async with httpx.AsyncClient(
            base_url="https://cognito-idp.us-east-1.amazonaws.com/"
        ) as client:
            return await client.get(
                f"{SECRETS['COGNITO_USER_POOL_ID']}/.well-known/jwks.json"
            ).json()

    # ---- 검사 개요 ---
    # 1. JWT 헤더를 디코딩해서 키 ID를 가져온다
    # 2. aws 에서 가져온 jwks에서 키 ID로 키를 가져온다!
    # 3. 이제 그 키로 JWT를 디코딩하고 서명을 검증하면 된다.


class FmpApi:
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


class WorldBankApi:
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
