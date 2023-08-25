import asyncio
from typing import List, Awaitable
from datetime import datetime

from backend.http import FmpApi
from backend.math import marge_lists
from backend.data.text import Multilingual
from backend.data.fmp.integrate import Symbol

__all__ = ["news"]


class News:
    def __init__(self, symbol, title, content, src, date: datetime):
        """
        - 인스턴스를 직접 생성하지 마세요. 함수를 통해 생성됩니다.
        - 인스턴스 생성 방법
            - `news = await News(...).load()`
        """
        self._symbol = symbol
        self.title = Multilingual(title)
        self.content = Multilingual(content)
        self.src = src
        self.date = date

    async def load(self):
        self.symbol = await Symbol(self._symbol).load()
        return self

    def __repr__(self):
        text_repr = (
            self.content.text
            if len(self.content.text) <= 30
            else self.content.text[:30] + "..."
        )
        return f"<News: {self.symbol.code} {self.date.strftime('%Y-%m-%d %H:%M')} '{text_repr}'>"


async def news(symbol: str, limit=10) -> List[News]:
    """
    - symbol: symbol에 대한 뉴스 리스트를 반환합니다.
        - symbol이 지정되지 않은 경우 최근 주식 뉴스들을 반환합니다.
    - limit: 반환될 최대 뉴스 갯수
    - return: 오래된 뉴스 -> 최신 뉴스로 정렬된 리스트
        - 컨벤션에 따라, 모든 시계열 정렬은 old -> new 입니다.
        - 뉴스가 없는 경우 빈 리스트
    """
    params = {"tickers": symbol, "limit": limit} if symbol else {"limit": limit}
    stock_resp, forex_resp, crypto_resp = await asyncio.gather(
        FmpApi(cache=False).get("api/v3/stock_news", **params),
        FmpApi(cache=False).get("api/v4/forex_news", **params),
        FmpApi(cache=False).get("api/v4/crypto_news", **params),
    )

    stock_news_loaders: List[Awaitable[News]] = []
    for news in stock_resp:
        if not news["symbol"]:
            continue  # symbol 매칭 가능한 뉴스만 수집할거임

        news = News(
            symbol=news["symbol"],
            title=news["title"],
            content=news["text"],
            src=news["url"],
            date=datetime.strptime(news["publishedDate"], "%Y-%m-%d %H:%M:%S"),
        ).load()
        stock_news_loaders.append(news)

    page = 0
    forex_news_loaders: List[Awaitable[News]] = []  # 외환 뉴스 수집
    while len(forex_news_loaders) < limit:
        params = {"symbol": symbol, "page": page}
        for news in forex_resp:
            forex_news_loaders.append(
                News(
                    symbol=symbol,
                    title=news["title"],
                    content=news["text"],
                    src=news["url"],
                    date=datetime.strptime(
                        news["publishedDate"], "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                ).load()
            )
            if len(forex_news_loaders) == limit:
                break
        if not forex_news_loaders:  # 한번 돌았는데 누적된게 없는 경우
            break  # 뉴스가 없는거니까 검색 중지
        page += 1

    page = 0
    crypto_news_loaders: List[Awaitable[News]] = []  # 암호화페 뉴스 수집
    while len(crypto_news_loaders) < limit:
        params = {"symbol": symbol, "page": page}
        for news in crypto_resp:
            crypto_news_loaders.append(
                News(
                    symbol=symbol,
                    title=news["title"],
                    content=news["text"],
                    src=news["url"],
                    date=datetime.strptime(
                        news["publishedDate"], "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                ).load()
            )
            if len(crypto_news_loaders) == limit:
                break
        if not crypto_news_loaders:  # 한번 돌았는데 누적된게 없는 경우
            break  # 뉴스가 없는거니까 검색 중지
        page += 1

    # 뉴스와 연관된 모든 Symbol들을 동시에 load 합니다.
    stock_news, forex_news, crypto_news = await asyncio.gather(
        asyncio.gather(*stock_news_loaders),
        asyncio.gather(*forex_news_loaders),
        asyncio.gather(*crypto_news_loaders),
    )

    total = marge_lists(stock_news, forex_news, crypto_news, limit=limit)
    return sorted(total, key=lambda news: news.date)
