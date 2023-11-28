""" /api/data """
import asyncio

from aiocache import cached

from backend.http import APIRouter
from backend.math import datetime2utcstr
from backend.data import fmp, world_bank
from backend.system import log

router = APIRouter("data")


@router.basic.get("/elements")
@cached(ttl=24 * 360)  # 실시간성이 없는 검색이므로 캐싱
async def search_symbols_and_countries(query: str, lang: str):
    """
    - 검색어(자연어)로 국가를 포함하는 시계열 요소들을 검색합니다.
    - query: 검색어
    - lang: 응답 데이터의 언어 (ISO 639-1)
    - Response: code, name, note를 가지는 요소들. countries와 symbols로 키가 분리되어 두개의 리스트로 제공
    """
    query = query.strip()

    async def parsing(obj):
        log.info(f"[시작][/elements] name, note 가져오기 -> {obj}")
        name, note = await asyncio.gather(obj.name.en(), obj.note.trans(to=lang))
        log.info(f"[완료][/elements] name, note 가져오기 -> {obj} -> {name}, {note}")
        return {
            "code": obj.code,
            "name": name,
            "note": note,
        }

    log.info(f"[시작] {query} symbol들과 country들을 fmp.search, world_bank.search를 통해 검색")
    symbol_objects, country_objects = await asyncio.gather(
        fmp.search(query), world_bank.search(query)
    )
    log.info(
        f"[완료] {query} symbol들과 country들을 fmp.search, world_bank.search를 통해 검색 -> {symbol_objects}, {country_objects}"
        f"[시작] 검색된 오브젝트들에서 JSON 파싱 가능한 객체로 파싱"
    )
    symbols, countries = await asyncio.gather(
        asyncio.gather(*[parsing(sym) for sym in symbol_objects]),
        asyncio.gather(*[parsing(ctry) for ctry in country_objects]),
    )
    log.info(f"[완료] {query} symbols={symbols}  countries={countries}")
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
        log.info(f"[시작][/news] title, content 가져오기 -> {obj}")
        title, content = await asyncio.gather(
            obj.title.trans(to=lang), obj.content.trans(to=lang)
        )
        log.info(f"[완료][/news] title, content 가져오기 -> {obj} -> {title}, {content}")
        return {
            "title": title,
            "content": content,
            "src": obj.src,
            "date": datetime2utcstr(obj.date),
        }

    log.info(f"[시작] {symbol} 객체 load, 뉴스 검색")
    symbol_obj, news_objects = await asyncio.gather(
        fmp.Symbol(code=symbol).load(), fmp.news(symbol)
    )
    log.info(
        f"[완료] {symbol} 객체 load, 뉴스 검색 -> {symbol_obj, news_objects}"
        f"[시작] {symbol} 객체 name, note 가져오기, 뉴스들 title, content 가져오기"
    )
    symbol_name, symbol_note, *news = await asyncio.gather(
        *[symbol_obj.name.en(), symbol_obj.note.trans(to=lang)]
        + [parsing(news_obj) for news_obj in news_objects]
    )
    log.info(
        f"[완료] {symbol} 객체 name, note 가져오기, 뉴스들 title, content 가져오기 -> {symbol_name}, {symbol_note}, {news}"
    )
    return {
        "contents": list(reversed(news)),  # 최신 -> 과거 순으로 정렬
        "symbol": {
            "code": symbol_obj.code,
            "name": symbol_name,
            "note": symbol_note,
        },
    }
