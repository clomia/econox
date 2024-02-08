""" 
- /api/data/...
- 데이터 제공합니다.
"""

import asyncio
from typing import Literal, List

import numpy as np
import xarray as xr
from aiocache import cached
from pydantic import BaseModel
from fastapi import HTTPException, Response, Query

from backend import db
from backend.http import APIRouter
from backend.calc import datetime2utcstr, denormalize
from backend.data import fmp, world_bank
from backend.system import ElasticRedisCache, CacheTTL, log
from backend.integrate import get_element, Feature, FeatureGroup


router = APIRouter("data")


@router.basic.get("/elements")
@cached(cache=ElasticRedisCache, ttl=CacheTTL.MID)  # 실시간성이 없는 검색이므로 캐싱
async def search_symbols_and_countries(
    query: str, lang: str = Query(..., min_length=2, max_length=2)
):
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
async def search_news_related_to_symbols(
    symbol: str, lang: str = Query(..., min_length=2, max_length=2)
):
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


class TimeSeries(BaseModel):
    v: List[float | int]
    t: List[str]


class FeatureTimeSeries(BaseModel):
    """시계열 데이터만"""

    original: TimeSeries
    normalized: TimeSeries


@router.basic.get("/feature")
async def get_feature_time_series(
    element_section: str, element_code: str, factor_section: str, factor_code: str
) -> FeatureTimeSeries:
    """
    - Element의 Factor 시계열 데이터를 응답합니다.
    - 해당 Element가 Factor를 지원하지 않는 경우 Element에서 Factor를 제거합니다.
        - 서버가 이 사실을 처음 알게 되었을때 수행됩니다.
    - response: {original: 원본 시계열, normalized: 표준화 시계열}
        - 각 시계열 안에는 동일한 길이의 값 배열(v)과 날짜 배열(t)이 들어있습니다.
    """
    feature = Feature(element_section, element_code, factor_section, factor_code)
    if (data := await feature.to_dataset()) is not None:
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


# 피쳐 그룹에 들어있는 피쳐들의 정보를 가져오는 쿼리
query_get_features_in_feature_group = """ 
    SELECT 
        e.section AS element_section,
        e.code AS element_code,
        f.section AS factor_section,
        f.code AS factor_code
    FROM feature_groups_features fgf
    JOIN elements_factors ef ON fgf.feature_id = ef.id
    JOIN elements e ON ef.element_id = e.id
    JOIN factors f ON ef.factor_id = f.id
    WHERE fgf.feature_group_id = {feature_group_id}
"""


class FeatureProperty(BaseModel):
    """시계열 데이터의 메타정보"""

    section: str
    code: str


class FeatureGroupTimeSeries(FeatureTimeSeries):
    ratio: TimeSeries


class GroupFeatureTimeSeries(FeatureGroupTimeSeries):
    """메타정보가 포함된 시계열 데이터"""

    element: FeatureProperty
    factor: FeatureProperty


@router.basic.get("/features")
async def get_feature_group_time_series(group_id: int) -> List[GroupFeatureTimeSeries]:
    """
    - 피쳐 그룹에 속한 모든 피쳐의 시계열 데이터를 응답합니다.
    - 응답 본문의 크기는 대략 5 ~ 10 MB 이내입니다.
        - 본문이 커서 swagger 문서가 응답을 표시하지 못합니다.
    - ratio는 해당 시점에서 피쳐의 비율을 나타냅니다. 0~1 사이의 실수입니다.
    """
    feature_attrs = await db.SQL(
        query_get_features_in_feature_group,
        params={"feature_group_id": group_id},
        fetch="all",
    ).exec()
    features = [Feature(**feature_attr) for feature_attr in feature_attrs]
    group = await FeatureGroup(*features).init()
    ds_original = group.to_dataset(normalized=False)
    ds_normalized = group.to_dataset(normalized=True)

    _sum = ds_original.to_array(dim="v").sum(
        dim="v"
    )  # 각 시점(t)에서 모든 변수의 합계를 계산
    ds_ratio = ds_original / _sum  # 각 변수를 해당 시점의 합계로 나누어 비율 계산

    result = []
    for feature in features:
        key = feature.repr_str()
        original = ds_original[key]
        normalized = ds_normalized[key]
        ratio = ds_ratio[key]
        result.append(
            {
                "element": {
                    "section": feature.element_section,
                    "code": feature.element_code,
                },
                "factor": {
                    "section": feature.factor_section,
                    "code": feature.factor_code,
                },
                "original": {
                    "v": original.values.tolist(),
                    "t": np.datetime_as_string(original.t.values, unit="D").tolist(),
                },
                "normalized": {
                    "v": normalized.values.tolist(),
                    "t": np.datetime_as_string(normalized.t.values, unit="D").tolist(),
                },
                "ratio": {
                    "v": ratio.values.tolist(),
                    "t": np.datetime_as_string(ratio.t.values, unit="D").tolist(),
                },
            }
        )
    return result


@router.professional.get("/feature/file")
async def download_feature_time_series(
    file_format: Literal["csv", "xlsx"],
    normalized: bool,
    element_section: str,
    element_code: str,
    factor_section: str,
    factor_code: str,
):
    """
    - Element의 Factor 시계열 데이터를 파일로 만들어서 응답합니다.
    - 파일 형식은 csv와 xlsx만 지원됩니다.
    """
    feature = Feature(element_section, element_code, factor_section, factor_code)

    func = {"csv": feature.to_csv, "xlsx": feature.to_xlsx}
    filename = f"{feature.element_code}-{feature.factor_section}-{feature.factor_code}"
    headers = {
        "csv": {"Content-Disposition": f"attachment; filename={filename}.csv"},
        "xlsx": {"Content-Disposition": f"attachment; filename={filename}.xlsx"},
    }
    media_type = {
        "csv": "text/csv",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }

    return Response(
        content=await func[file_format](normalized),
        media_type=media_type[file_format],
        headers=headers[file_format],
    )


@router.professional.get("/features/file")
async def download_feature_group_time_series(
    file_format: Literal["csv", "xlsx"],
    normalized: bool,
    group_id: int,
    lang: str = Query(..., min_length=2, max_length=2),
):
    """
    - 피쳐 그룹에 속한 모든 피쳐의 시계열 데이터를 파일로 만들어서 응답합니다.
    - 파일 형식은 csv와 xlsx만 지원됩니다.
    """
    feature_attrs = await db.SQL(
        query_get_features_in_feature_group,
        params={"feature_group_id": group_id},
        fetch="all",
    ).exec()
    features = [Feature(**feature_attr) for feature_attr in feature_attrs]
    group = await FeatureGroup(*features).init()

    func = {"csv": group.to_csv, "xlsx": group.to_xlsx}
    headers = {
        "csv": {"Content-Disposition": f"attachment; filename=group({group_id}).csv"},
        "xlsx": {"Content-Disposition": f"attachment; filename=group({group_id}).xlsx"},
    }
    media_type = {
        "csv": "text/csv",
        "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    }

    return Response(
        content=await func[file_format](lang=lang, normalized=normalized),
        media_type=media_type[file_format],
        headers=headers[file_format],
    )
