import asyncio
from typing import List
from datetime import datetime

from backend.http import FmpAPI
from backend.math import marge_lists
from backend.data.text import Multilingual

__all__ = ["news"]


class News:
    def __init__(self, symbol: str, title: str, content: str, src: str, date: datetime):
        """
        - 인스턴스를 직접 생성하지 마세요. 함수를 통해 생성됩니다.
        """
        self.symbol = symbol
        self.title = Multilingual(title)
        self.content = Multilingual(content)
        self.src = src
        self.date = date

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
    stock_resp, forex_resp, crypto_resp = await asyncio.gather(
        FmpAPI(cache=False).get("api/v3/stock_news", tickers=symbol, limit=limit),
        FmpAPI(cache=False).get("api/v4/forex_news", symbol=symbol),
        FmpAPI(cache=False).get("api/v4/crypto_news", symbol=symbol),
    )

    stock_news: List[News] = []
    for news in stock_resp:
        if not news["symbol"]:
            continue  # symbol 매칭 가능한 뉴스만 수집할거임

        news = News(
            symbol=news["symbol"],
            title=news["title"],
            content=news["text"],
            src=news["url"],
            date=datetime.strptime(news["publishedDate"], "%Y-%m-%d %H:%M:%S"),
        )
        stock_news.append(news)

    page = 0
    forex_news: List[News] = []  # 외환 뉴스 수집
    while len(forex_news) < limit:
        params = {"symbol": symbol, "page": page}
        for news in forex_resp:
            forex_news.append(
                News(
                    symbol=symbol,
                    title=news["title"],
                    content=news["text"],
                    src=news["url"],
                    date=datetime.strptime(
                        news["publishedDate"], "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                )
            )
            if len(forex_news) == limit:
                break
        if not forex_news:  # 한번 돌았는데 누적된게 없는 경우
            break  # 뉴스가 없는거니까 검색 중지
        page += 1

    page = 0
    crypto_news: List[News] = []  # 암호화페 뉴스 수집
    while len(crypto_news) < limit:
        params = {"symbol": symbol, "page": page}
        for news in crypto_resp:
            crypto_news.append(
                News(
                    symbol=symbol,
                    title=news["title"],
                    content=news["text"],
                    src=news["url"],
                    date=datetime.strptime(
                        news["publishedDate"], "%Y-%m-%dT%H:%M:%S.%fZ"
                    ),
                )
            )
            if len(crypto_news) == limit:
                break
        if not crypto_news:  # 한번 돌았는데 누적된게 없는 경우
            break  # 뉴스가 없는거니까 검색 중지
        page += 1
    print(len(stock_news), len(forex_news), len(crypto_news))
    total = marge_lists(stock_news, forex_news, crypto_news, limit=limit)
    return sorted(total, key=lambda news: news.date)
