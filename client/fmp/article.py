import os
from datetime import datetime
from typing import List

import requests

from client.translate import Multilingual
from client.fmp.integrate import Symbol

HOST = "https://financialmodelingprep.com"
assert (API_KEY := os.getenv("FMP_API_KEY"))  # FMP_API_KEY 환경변수가 정의되지 않았습니다!

__all__ = ["news"]


def request(url: str, params: dict = {}):
    """
    - url: HOST를 제외하고 양 끝 "/"가 없는 url
    - params: apikey를 제외한 URL 쿼리 파라미터들
    """
    response = requests.get(f"{HOST}/{url}", params=params | {"apikey": API_KEY})
    response.raise_for_status()  # FMP 서버의 응답이 잘못된 경우 HTTPError
    return response.json()


class News:
    def __init__(self, symbol, title, content, src, date: datetime):
        """인스턴스를 직접 생성하지 마세요. 함수를 통해 생성됩니다."""
        self.symbol = Symbol(symbol)
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


def news(symbol=None, limit=10) -> List[News]:
    """
    - symbol: symbol에 대한 뉴스 리스트를 반환합니다.
        - symbol이 지정되지 않은 경우 최근 주식 뉴스들을 반환합니다.
    - limit: 반환될 최대 뉴스 갯수
    - return: 오래된 뉴스 -> 최신 뉴스로 정렬된 리스트
        - 컨벤션에 따라, 모든 시계열 정렬은 old -> new 입니다.
        - 뉴스가 없는 경우 빈 리스트
    """
    params = {"tickers": symbol, "limit": limit} if symbol else {"limit": limit}
    stock_news = [  # 일반 주식 뉴스 수집
        News(
            symbol=news["symbol"],
            title=news["title"],
            content=news["text"],
            src=news["url"],
            date=datetime.strptime(news["publishedDate"], "%Y-%m-%d %H:%M:%S"),
        )
        for news in request("api/v3/stock_news", params=params)
        if news["symbol"]
    ]
    if not symbol:
        # 다른 API는 최신 뉴스에 symbol이 많이 비어있어서 stock_news만 사용
        return sorted(stock_news, key=lambda news: news.date)

    page = 0
    forex_news = []  # 외환 뉴스 수집
    while len(forex_news) < limit:
        params = {"symbol": symbol, "page": page}
        for news in request("api/v4/forex_news", params=params):
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
    crypto_news = []  # 암호화페 뉴스 수집
    while len(crypto_news) < limit:
        params = {"symbol": symbol, "page": page}
        for news in request("api/v4/crypto_news", params=params):
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

    total = (stock_news + forex_news + crypto_news)[:limit]
    return sorted(total, key=lambda news: news.date)
