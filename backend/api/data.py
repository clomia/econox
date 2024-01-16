""" /api/data """
import asyncio

import numpy as np
import xarray as xr
from aiocache import cached
from fastapi import HTTPException

from backend import db
from backend.http import APIRouter
from backend.math import datetime2utcstr, denormalize
from backend.data import fmp, world_bank
from backend.data.model import Factor
from backend.system import ElasticRedisCache, CacheTTL, log
from backend.integrate import get_element


router = APIRouter("data")


@router.basic.get("/elements")
@cached(cache=ElasticRedisCache, ttl=CacheTTL.MID)  # 실시간성이 없는 검색이므로 캐싱
async def search_symbols_and_countries(query: str, lang: str):
    """
    - 검색어(자연어)로 국가를 포함하는 시계열 요소들을 검색합니다.
    - query: 검색어
    - lang: 응답 데이터의 언어 (ISO 639-1)
    - Response: code, name, note를 가지는 요소들. countries와 symbols로 키가 분리되어 두개의 리스트로 제공
    """
    query = query.strip()

    async def parsing(obj):
        name, note = await asyncio.gather(obj.name.en(), obj.note.trans(to=lang))
        return {
            "code": obj.code,
            "name": name,
            "note": note,
        }

    symbol_objects, country_objects = await asyncio.gather(
        fmp.search(query), world_bank.search(query), return_exceptions=True
    )  # search 메서드는 API 요청이 매우 많으므로 실패할때를 대비해야 한다.
    if isinstance(symbol_objects, Exception):
        log.error(
            "FMP 검색에 실패했습니다. 빈 배열로 대체합니다. "
            f"{symbol_objects.__class__.__name__}: {symbol_objects}"
        )
        symbol_objects = []
    if isinstance(country_objects, Exception):
        log.error(
            "World Bank 검색에 실패했습니다. 빈 배열로 대체합니다. "
            f"{country_objects.__class__.__name__}: {country_objects}"
        )
        country_objects = []
    symbols, countries = await asyncio.gather(  # 이건 단순한 번역이라 괜찮음
        asyncio.gather(*[parsing(sym) for sym in symbol_objects]),
        asyncio.gather(*[parsing(ctry) for ctry in country_objects]),
    )
    return {
        "symbols": symbols,
        "countries": countries,
    }


@router.basic.get("/news")
async def search_news_related_to_symbols(symbol: str, lang: str):
    """
    - symbol에 대한 최신 뉴스들을 가져옵니다. (국가에 대한 뉴스는 지원되지 않음)
    - lang: 응답 데이터의 언어 (ISO 639-1)
    """

    async def parsing(obj):
        title, content = await asyncio.gather(
            obj.title.trans(to=lang), obj.content.trans(to=lang)
        )
        return {
            "title": title,
            "content": content,
            "src": obj.src,
            "date": datetime2utcstr(obj.date),
        }

    symbol_obj, news_objects = await asyncio.gather(
        get_element(section="symbol", code=symbol), fmp.news(symbol)
    )

    symbol_name, symbol_note, *news = await asyncio.gather(
        *[symbol_obj.name.en(), symbol_obj.note.trans(to=lang)]
        + [parsing(news_obj) for news_obj in news_objects]
    )
    return {
        "contents": list(reversed(news)),  # 최신 -> 과거 순으로 정렬
        "symbol": {
            "code": symbol_obj.code,
            "name": symbol_name,
            "note": symbol_note,
        },
    }


# 다변량은 GET /data/features 로 만들자


@router.basic.get("/feature")
async def get_feature_time_series(
    element_code: str, element_section: str, factor_code: str, factor_section: str
):
    """
    - Element의 Factor 시계열 데이터를 응답합니다.
    - 해당 Element가 Factor를 지원하지 않는 경우 Element에서 Factor를 제거합니다.
        - 서버가 이 사실을 처음 알게 되었을때 수행됩니다.
    - response: {original: 원본 시계열, normalized: 표준화 시계열}
        - 각 시계열 안에는 동일한 길이의 값 배열(v)과 날짜 배열(t)이 들어있습니다.
    """
    element = await get_element(element_section, element_code)
    # ClientMeta 메타클래스가 만든 data_class 클래스의 인스턴스
    try:
        data_instance = getattr(element, element.attr_name[factor_section])
        factor: Factor = getattr(data_instance, factor_code)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"factor_section {factor_section} does not exist"
        )
    except AttributeError:
        raise HTTPException(
            status_code=404, detail=f"factor_code {factor_code} does not exist"
        )

    data: xr.Dataset = await factor.get()
    if data is not None:
        original = denormalize(data)
        normalized: xr.DataArray = data.daily
        return {
            "original": {
                "v": original.values.tolist(),
                "t": np.datetime_as_string(original.t.values, unit="D").tolist(),
            },
            "normalized": {
                "v": normalized.values.tolist(),
                "t": np.datetime_as_string(normalized.t.values, unit="D").tolist(),
            },
        }
    else:
        await db.SQL(
            """
        DELETE FROM elements_factors
        WHERE element_id = (
            SELECT id FROM elements
            WHERE code = {ec}
            AND section = {es}
        )
        AND factor_id = (
            SELECT id FROM factors
            WHERE code = {fc}
            AND section = {fs}
        )""",
            params={
                "ec": element_code,
                "es": element_section,
                "fc": factor_code,
                "fs": factor_section,
            },
        ).exec()
        raise HTTPException(
            status_code=404,
            detail=f"The {factor_code} factor is not supported by this element",
        )
