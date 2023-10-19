""" /api/data """
import asyncio

from aiocache import cached
from fastapi import Body, HTTPException

from backend.http import APIRouter
from backend.math import datetime2utcstr
from backend.data import fmp, world_bank

router = APIRouter("data")


@router.basic.get("/elements")
@cached(ttl=24 * 360)  # 실시간성이 없는 검색이므로 캐싱
async def search_symbols_and_countries(query: str, lang: str):
    async def parsing(obj):
        name, note = await asyncio.gather(obj.name.en(), obj.note.trans(to=lang))
        return {
            "code": obj.code,
            "name": name,
            "note": note,
        }

    symbol_objects, country_objects = await asyncio.gather(
        fmp.search(query), world_bank.search(query)
    )
    symbols, countries = await asyncio.gather(
        asyncio.gather(*[parsing(sym) for sym in symbol_objects]),
        asyncio.gather(*[parsing(ctry) for ctry in country_objects]),
    )
    return {
        "symbols": symbols,
        "countries": countries,
    }


@router.basic.get("/news")
async def search_news_related_to_symbols(symbol: str, lang: str):
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
        fmp.Symbol(code=symbol).load(), fmp.news(symbol)
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
