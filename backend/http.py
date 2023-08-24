""" API 통신에 반복적으로 필요한 로직 모듈화 """
import asyncio
from functools import partial

import httpx
import wbdata
from aiocache import cached

from backend.system import SECRETS, log, Parallel


class FmpApi:
    """financialmodelingprep API GET Request"""

    def __init__(self, cache: bool):
        self.cache = cache

    async def get(self, path, **params) -> dict | list:
        request = self._request_use_caching if self.cache else self._request
        for interval in [0, 0.2, 0.5, 1, 3, 5, 7, 10, 25, 60, 0]:
            try:
                return await request(path, **params)
            except Exception as error:
                log.warning(
                    "FMP API 서버와 통신에 실패했습니다."
                    f"{interval}초 후 다시 시도합니다... (path: {path})"
                )
                asyncio.sleep(interval)  # retry 대기
                continue
        else:  # 끝까지 통신에 실패하면 에러 raise
            log.error(f"FMP API 서버와 통신에 실패하여 데이터를 수신하지 못했습니다. (path: {path})")
            raise error

    async def _request(self, path, **params) -> dict:
        async with httpx.AsyncClient(
            base_url="https://financialmodelingprep.com",
            params={"apikey": SECRETS["FMP_API_KEY"]},
        ) as fmp_client:
            response = await fmp_client.get(path, params)
            response.raise_for_status()
        return response.json()

    @cached(ttl=12 * 360)
    async def _request_use_caching(self, path, **params):
        return await self._request(path, **params)


class WorldBankApi:
    @cached(ttl=12 * 360)
    async def get_data(self, indicator, country) -> list:
        """국가의 지표 시계열을 반환합니다."""
        func = partial(self._safe_caller(wbdata.get_data), indicator, country)
        return (await Parallel(Async=True).execute(func))[func]

    @cached(ttl=12 * 360)
    async def get_indicator(self, indicator) -> dict:
        """지표에 대한 상세 정보를 반환합니다."""
        func = partial(self._safe_caller(wbdata.get_indicator), indicator)
        return (await Parallel(Async=True).execute(func))[func][0]

    @cached(ttl=12 * 360)
    async def search_countries(self, text) -> dict:
        """자연어로 국가들을 검색합니다."""
        func = partial(self._safe_caller(wbdata.search_countries), text)
        return (await Parallel(Async=True).execute(func))[func]?

    @cached(ttl=12 * 360)
    async def get_country(self, code) -> dict:
        """국가 코드에 해당하는 국가를 반환합니다.."""
        func = partial(self._safe_caller(wbdata.get_country), code)
        return (await Parallel(Async=True).execute(func))[func][0]

    @staticmethod
    def _safe_caller(wb_func):
        """
        - wbdata 함수가 안전하게 작동하도록 감쌉니다.
        - wbdata 라이브러리의 캐싱 알고리즘은 thread-safe하지 않으므로
        항상 cache=False 해줘야 하며, 결과가 없을 때 RuntimeError를 발생시키는데
        에러를 발생시키는 대신에 빈 리스트를 반환하도록 변경합니다.
        """

        def wrapper(*args, **kwargs):
            try:
                return wb_func(*args, **kwargs, cache=False)
            except RuntimeError:
                return []

        return wrapper
