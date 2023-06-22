""" 모든 data_class를 Symbol 객체로 통합 """
from __future__ import annotations

import os
import json
from typing import List, Any
from functools import lru_cache

import requests
import pycountry

from client.fmp import data_metaclass
from config import LRU_CACHE_SIZE
from client.translate import Multilingual, translator

API_KEY = os.getenv("FMP_API_KEY")
HOST = "https://financialmodelingprep.com"

# ========= data_class.json에 정의된 클래스들을 생성합니다. =========
classes = dict(json.load(data_metaclass.CLASS_PATH.open("rb")))


def create_class(name: str) -> type:
    """메타클래스로 data_class.json에 정의된 클래스를 생성합니다."""
    config = classes[name]
    meta = getattr(data_metaclass, config["setting"]["metaclass"])
    return meta(name)


InstitutionalStockOwnership = create_class("InstitutionalStockOwnership")
UsaEconomicIndicator = create_class("UsaEconomicIndicator")
UsaTreasuryRates = create_class("UsaTreasuryRates")
StockMarketSectorsPerformance = create_class("StockMarketSectorsPerformance")
HistoricalDividends = create_class("HistoricalDividends")
AdvancedLeveredDiscountedCashFlow = create_class("AdvancedLeveredDiscountedCashFlow")
AdvancedDiscountedCashFlow = create_class("AdvancedDiscountedCashFlow")
MarketCapitalization = create_class("MarketCapitalization")
EsgScore = create_class("EsgScore")
CotReportAnalysis = create_class("CotReportAnalysis")
CotReport = create_class("CotReport")
EarningsCalendar = create_class("EarningsCalendar")
CashFlowStatement = create_class("CashFlowStatement")
BalanceSheetStatement = create_class("BalanceSheetStatement")
IncomeStatement = create_class("IncomeStatement")
FinancialRatios = create_class("FinancialRatios")
CashFlowStatementGrowth = create_class("CashFlowStatementGrowth")
BalanceSheetStatementGrowth = create_class("BalanceSheetStatementGrowth")
IncomeStatementGrowth = create_class("IncomeStatementGrowth")
FinancialGrowth = create_class("FinancialGrowth")
AnalystEstimates = create_class("AnalystEstimates")
ReportedIncomeStatements = create_class("ReportedIncomeStatements")
CompanyRating = create_class("CompanyRating")
DiscountedCashFlow = create_class("DiscountedCashFlow")
NumberOfEmployees = create_class("NumberOfEmployees")
CompanyKeyMetrics = create_class("CompanyKeyMetrics")
CompanyEnterpriseValue = create_class("CompanyEnterpriseValue")
HistoricalPrice = create_class("HistoricalPrice")
# =====================================================================


@lru_cache(maxsize=LRU_CACHE_SIZE)
def _cache_request(url, **params):
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def _normal_request(url, **params):
    response = requests.get(url, params=params)
    response.raise_for_status()
    return response.json()


def request(url: str, default=None, cache=False, **params: dict) -> dict | list | Any:
    """
    - url: HOST를 제외하고 양 끝 "/"가 없는 url
    - params: apikey를 제외한 URL 쿼리 파라미터들
    - default: 값이 없을 때 반환됩니다
    """
    get_func = _cache_request if cache else _normal_request
    data = get_func(f"{HOST}/{url}", **params | {"apikey": API_KEY})
    return data if data else default


class Symbol:
    def __init__(self, symbol: str):
        self.symbol = symbol

        # 주식 관련
        self.price = HistoricalPrice(symbol)
        self.dividends = HistoricalDividends(symbol)
        self.enterprise_value = CompanyEnterpriseValue(symbol)

        # 재무 요약
        self.key_metrics = CompanyKeyMetrics(symbol)
        self.financial_ratio = FinancialRatios(symbol)
        self.financial_growth = FinancialGrowth(symbol)

        # 현금 흐름표
        self.cash_flow = CashFlowStatement(symbol)
        self.cash_flow_growth = CashFlowStatementGrowth(symbol)

        # 대차대조표
        self.balance_sheet = BalanceSheetStatement(symbol)
        self.balance_sheet_growth = BalanceSheetStatementGrowth(symbol)

        # 수입
        self.income = IncomeStatement(symbol)
        self.reported_income = ReportedIncomeStatements(symbol)
        self.income_growth = IncomeStatementGrowth(symbol)
        self.earnings = EarningsCalendar(symbol)

        # 사회적 요소
        self.institutional_ownership = InstitutionalStockOwnership(symbol)
        self.employees = NumberOfEmployees(symbol)

        # 기업 평가
        self.dcf = AdvancedDiscountedCashFlow(symbol)
        self.levered_dcf = AdvancedLeveredDiscountedCashFlow(symbol)
        self.rating = CompanyRating(symbol)
        self.esg_score = EsgScore(symbol)

        # 분석
        self.cot_report_analysis = CotReportAnalysis(symbol)
        self.cot_report = CotReport(symbol)
        self.analyst_estimates = AnalystEstimates(symbol)

    def __repr__(self) -> str:
        return f"<Symbol: {self.symbol}>"

    @property
    def info(self) -> dict:
        """
        - API 호출을 통해 symbol에 대한 name, currency, note, country, is_company를 취득합니다.
        - 이미 취득된 데이터는 메모리에 캐싱됩니다.
        """
        info = request(url="api/v4/company-outlook", symbol=self.symbol, cache=True)

        name = note = country = "No information"
        currency = "USD"
        is_company = False
        if profile := info.get("profile"):
            name = profile["companyName"]
            currency = profile["currency"]
            note = profile["description"]
            if profile["country"]:
                country = pycountry.countries.get(alpha_2=profile["country"]).alpha_3
            is_company = bool(profile["industry"])  # company-outlook애 industry있으면 기업임
        elif info := request(url="api/v3/search", query=self.symbol, cache=True):
            name = info[0]["name"]
            currency = info[0]["currency"]
            note = f"{info[0]['stockExchange']} - {name}"
        return {
            "name": name,
            "note": note,
            "currency": currency,
            "country": country,
            "is_company": is_company,
        }

    @property
    def name(self):
        """Symbol 이름"""
        return Multilingual(self.info["name"])

    @property
    def note(self):
        """Symbol 설명"""
        return Multilingual(self.info["note"])

    @property
    def currency(self):
        """Symbol에 대해 사용되는 통화"""
        return self.info["currency"]

    @property
    def country(self):
        """Symbol 국가"""
        return self.info["country"]

    @property
    def is_company(self) -> bool:
        """Symbol의 기업 여부"""
        return self.info["is_company"]

    @property
    def peers(self) -> List[Symbol]:
        """
        - api/v4/stock_peers
        - 자신과 관련된 Symbol 리스트
        """
        response = request("api/v4/stock_peers", symbol=self.symbol, cache=True)
        return (
            [self.__class__(symbol) for symbol in response[0]["peersList"]]
            if response
            else []
        )

    @property
    def current_price(self) -> float | None:
        """
        - api/v3/quote
        - 현재가격
        """
        response = request(f"api/v3/quote-short/{self.symbol}")
        return float(response[0]["price"]) if response else None

    @property
    def current_change(self) -> float | None:
        """
        - api/v3/quote
        - 현재 가격 변화율 (%)
        """
        response = request(f"api/v3/quote/{self.symbol}")
        return float(response[0]["changesPercentage"]) if response else None


def search(text: str, limit: int = 10) -> List[Symbol]:
    """
    - api/v3/search
    - text: 검색 문자열
        - 다국어 가능!
    - limit: 검색 결과 갯수 제한
    - 검색 결과가 없으면 빈 리스트를 반환합니다.
    """
    en_text = translator(text, to_lang="en")
    response = request("api/v3/search", query=en_text, limit=limit, cache=True)
    return [Symbol(ele["symbol"]) for ele in response] if response else []


filter_params = {
    "sectors": [
        "Consumer Cyclical",
        "Energy",
        "Technology",
        "Industrials",
        "Financial Services",
        "Basic Materials",
        "Communication Services",
        "Consumer Defensive",
        "Healthcare",
        "Real Estate",
        "Utilities",
        "Industrial Goods",
        "Financial",
        "Services",
        "Conglomerates",
    ],
    "industries": [
        "Autos",
        "Banks",
        "Banks Diversified",
        "Software",
        "Banks Regional",
        "Beverages Alcoholic",
        "Beverages Brewers",
        "Beverages Non",
        "Alcoholic",
    ],
    "exchanges": ["nyse", "nasdaq", "amex", "euronext", "tsx", "etf", "mutual_fund"],
}


def cond_search(
    min_market_cap: float = None,
    max_market_cap: float = None,
    min_price: float = None,
    max_price: float = None,
    min_beta: float = None,
    max_beta: float = None,
    min_volume: float = None,
    max_volume: float = None,
    min_dividend: float = None,
    max_dividend: float = None,
    is_etf: bool = None,
    is_actively: bool = None,
    sector: str = None,
    industry: str = None,
    country: str = None,
    exchange: str = None,
    limit: int = None,
) -> List[Symbol]:
    """
    - api/v3/stock-screener
    - 검색 결과가 없으면 빈 리스트를 반환합니다.
    - sector, industry, exchange 매개변수에 대해서는 filter_params를 참조하세요
    - country: 국가 코드(ISO 3166-1 alpha-3)
    """

    assert sector is None or sector in filter_params["sectors"]
    assert industry is None or industry in filter_params["industries"]
    assert exchange is None or exchange in filter_params["exchanges"]
    if country:  # FMP에서는 alpha-2 코드를 쓰기 때문에 변환
        country = pycountry.countries.get(alpha_3=country).alpha_2

    make_params = lambda *arg_name: {name: arg for name, arg in arg_name if arg}
    params = make_params(
        ("marketCapMoreThan", min_market_cap),
        ("marketCapLowerThan", max_market_cap),
        ("priceMoreThan", min_price),
        ("priceLowerThan", max_price),
        ("betaMoreThan", min_beta),
        ("betaLowerThan", max_beta),
        ("volumeMoreThan", min_volume),
        ("volumeLowerThan", max_volume),
        ("dividendMoreThan", min_dividend),
        ("dividendLowerThan", max_dividend),
        ("isEtf", is_etf),
        ("isActivelyTrading", is_actively),
        ("sector", sector),
        ("industry", industry),
        ("country", country),
        ("exchange", exchange),
        ("limit", limit),
    )
    response = request("api/v3/stock-screener", **params, cache=True)
    return [Symbol(ele["symbol"]) for ele in response] if response else []


def _get_list(url: str, key="symbol"):
    return [Symbol(ele[key]) for ele in response] if (response := request(url)) else []


def list_gainers() -> List[Symbol]:
    """
    - api/v3/stock_market/gainers
    - 급상승 종목들
    """
    return _get_list("api/v3/stock_market/gainers")


def list_losers() -> List[Symbol]:
    """
    - api/v3/stock_market/losers
    - 급하락 종목들
    """
    return _get_list("api/v3/stock_market/losers")


def list_actives() -> List[Symbol]:
    """
    - api/v3/stock_market/actives
    - 현재 거래량이 가장 많은 종목들
    """
    return _get_list("api/v3/stock_market/actives")


def list_all() -> List[Symbol]:
    """
    - api/v3/stock/list
    - 사용 가능한 모든 symbol 리스트
    - 주의: 4분 이상 소요됨.
    - 리스트 길이: 약 7만개
    """
    return _get_list("api/v3/stock/list")


def list_cot() -> List[Symbol]:
    """api/v4/commitment_of_traders_report/list"""
    return _get_list("api/v4/commitment_of_traders_report/list", key="trading_symbol")


def list_tradable() -> List[Symbol]:
    """
    - api/v3/available-traded/list
    - 주의: 2분 이상 소요됨.
    - 리스트 길이: 약 5만 3천개
    """
    return _get_list("api/v3/available-traded/list")


def list_etf() -> List[Symbol]:
    """api/v3/etf/list"""
    return _get_list("api/v3/etf/list")


def list_sp500() -> List[Symbol]:
    """api/v3/sp500_constituent"""
    return _get_list("api/v3/sp500_constituent")


def list_nasdaq() -> List[Symbol]:
    """api/v3/nasdaq_constituent"""
    return _get_list("api/v3/nasdaq_constituent")


def list_dowjones() -> List[Symbol]:
    """api/v3/dowjones_constituent"""
    return _get_list("api/v3/dowjones_constituent")


def list_index() -> List[Symbol]:
    """api/v3/symbol/available-indexes"""
    return _get_list("api/v3/symbol/available-indexes")


def list_euronext() -> List[Symbol]:
    """api/v3/symbol/available-euronext"""
    return _get_list("api/v3/symbol/available-euronext")


def list_tsx() -> List[Symbol]:
    """api/v3/symbol/available-tsx"""
    return _get_list("api/v3/symbol/available-tsx")


def list_crypto() -> List[Symbol]:
    """api/v3/symbol/available-cryptocurrencies"""
    return _get_list("api/v3/symbol/available-cryptocurrencies")


def list_forex() -> List[Symbol]:
    """api/v3/symbol/available-forex-currency-pairs"""
    return _get_list("api/v3/symbol/available-forex-currency-pairs")


def list_commodity() -> List[Symbol]:
    """api/v3/symbol/available-commodities"""
    return _get_list("api/v3/symbol/available-commodities")
