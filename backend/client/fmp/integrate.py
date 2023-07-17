""" 모든 data_class를 Symbol 객체로 통합 """
from __future__ import annotations

import os
import json
import time
from typing import List
from functools import lru_cache, partial

import requests
import pycountry

from backend.system import LRU_CACHE_SIZE, INFO_PATH, log
from backend.compute import parallel
from backend.client.fmp import data_metaclass
from backend.client.translate import Multilingual, translator

HOST = "https://financialmodelingprep.com"
assert (API_KEY := os.getenv("FMP_API_KEY"))  # FMP_API_KEY 환경변수가 정의되지 않았습니다!

# ========= data_class.json에 정의된대로 클래스들을 생성합니다. =========
classes = dict(json.load(data_metaclass.CLASS_PATH.open("r")))


def create_class(name: str) -> type:
    """메타클래스로 data_class.json에 정의된 클래스를 생성합니다."""
    config = classes[name]
    meta = getattr(data_metaclass, config["setting"]["metaclass"])
    return meta(name)


InstitutionalStockOwnership = create_class("InstitutionalStockOwnership")
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


def request(url: str, default=None, cache=False, **params: dict):
    """
    - url: HOST를 제외하고 양 끝 "/"가 없는 url
    - params: apikey를 제외한 URL 쿼리 파라미터들
    - default: 값이 없을 때 반환됩니다
    """
    get_func = _cache_request if cache else _normal_request

    # 실패 시 이정도 간격을 두고 10번 더 재시도
    retry_interval = [0, 0.5, 1, 5, 10, 15, 20, 25, 30, 60]
    for interval in retry_interval + [0]:  # 마지막은 continue 못하니까
        try:
            data = get_func(f"{HOST}/{url}", **params | {"apikey": API_KEY})
        except Exception as error:
            log.warning(
                f"FMP API 서버와 통신에 실패했습니다. {interval}초 후 다시 시도합니다... (URL: {url})"
            )
            time.sleep(interval)  # retry 대기
            continue
        else:  # 성공
            break
    else:  # 끝까지 통신에 실패하면 에러 raise
        log.error(f"FMP API 서버와 통신에 실패하여 데이터를 수신하지 못했습니다. (URL: {url})")
        raise error
    return data if data else default


class Symbol:
    def __init__(self, code: str):
        self.code = code
        self.info_path = INFO_PATH / f"symbol/{code}.json"
        self.info = self.get_info()
        self.is_valid = self.info["name"] and self.info["note"]

        # 주식 관련
        self.price = HistoricalPrice(code)
        self.dividends = HistoricalDividends(code)
        self.enterprise_value = CompanyEnterpriseValue(code)

        # 재무 요약
        self.key_metrics = CompanyKeyMetrics(code)
        self.financial_ratio = FinancialRatios(code)
        self.financial_growth = FinancialGrowth(code)

        # 현금 흐름표
        self.cash_flow = CashFlowStatement(code)
        self.cash_flow_growth = CashFlowStatementGrowth(code)

        # 대차대조표
        self.balance_sheet = BalanceSheetStatement(code)
        self.balance_sheet_growth = BalanceSheetStatementGrowth(code)

        # 수입
        self.income = IncomeStatement(code)
        self.reported_income = ReportedIncomeStatements(code)
        self.income_growth = IncomeStatementGrowth(code)
        self.earnings = EarningsCalendar(code)

        # 사회적 요소
        self.institutional_ownership = InstitutionalStockOwnership(code)
        self.employees = NumberOfEmployees(code)

        # 기업 평가
        self.dcf = AdvancedDiscountedCashFlow(code)
        self.levered_dcf = AdvancedLeveredDiscountedCashFlow(code)
        self.rating = CompanyRating(code)
        self.esg_score = EsgScore(code)

        # 분석
        self.cot_report_analysis = CotReportAnalysis(code)
        self.cot_report = CotReport(code)
        self.analyst_estimates = AnalystEstimates(code)

    def __repr__(self) -> str:
        return f"<Symbol: {self.code}>"

    def get_info(self):
        """
        - name과 note정보를 수집해서 정제한 뒤 반환합니다.
        - efs-volume에 캐싱을 하여 API 호출을 반복하지 않도록 합니다.
        - api/v3/profile API로 검색하고 정보가 없다면 api/v3/search로 다시 검색합니다.
        """

        # ======= EFS volume 에서 가져오기 =======
        if self.info_path.exists():  # 볼륨에서 가져오기
            return json.load(self.info_path.open("r"))

        # ======= API 사용해서 데이터 수집 =======
        res = parallel.executor(
            profile_api := partial(request, f"api/v3/profile/{self.code}"),
            search_api := partial(request, "api/v3/search", query=self.code),
        )
        profile_info = res[profile_api]
        search_info = res[search_api]

        name = exchange = currency = description = None
        if profile_info:
            name = profile_info[0]["companyName"]
            exchange = profile_info[0]["exchange"]
            currency = profile_info[0]["currency"]
            description = profile_info[0]["description"]
        elif search_info:
            if matched := [ele for ele in search_info if ele["symbol"] == self.code]:
                name = matched[0]["name"]
                exchange = matched[0]["stockExchange"]
                currency = matched[0]["currency"]

        # ======= 수집된 데이터 정제 =======
        currency_obj = pycountry.currencies.get(alpha_3=currency) if currency else None
        if name and exchange and currency_obj:  # 이 3가지 정보는 필수
            note_basic = f"{name}({self.code}) is traded at {exchange} and the currency uses {currency_obj.name}"
            note = f"{note_basic} {description}" if description else note_basic
            info = {"name": name, "note": note}
        else:
            info = {"name": name, "note": None}  # name은 None일 수도 있음
        self.info_path.parent.mkdir(parents=True, exist_ok=True)
        json.dump(info, self.info_path.open("w"))  # EFS volume에 저장
        return info

    @property
    def name(self):
        _name = self.info["name"]
        return Multilingual(_name if _name else f"{self.code}: No information")

    @property
    def note(self):
        _note, _name = self.info["note"], self.info["name"]
        if _note:
            return Multilingual(_note)
        elif _name:
            return Multilingual(f"{_name}({self.code}): No information")
        else:
            return Multilingual(f"{self.code}: No information")

    @property
    def peers(self) -> List[Symbol]:
        """
        - api/v4/stock_peers
        - 자신과 관련된 Symbol 리스트
        """
        response = request("api/v4/stock_peers", symbol=self.code, cache=True)
        return self._from_list(response[0]["peersList"]) if response else []

    @property
    def current_price(self) -> float | None:
        """
        - api/v3/quote
        - 현재가격
        """
        response = request(f"api/v3/quote-short/{self.code}")
        return float(response[0]["price"]) if response else None

    @property
    def current_change(self) -> float | None:
        """
        - api/v3/quote
        - 현재 가격 변화율 (%)
        """
        response = request(f"api/v3/quote/{self.code}")
        return float(response[0]["changesPercentage"]) if response else None

    @classmethod
    def _from_list(cls, _list, key=None) -> List[Symbol]:
        """
        - FMP API 응답 리스트를 Symbol 리스트로 만들기 위해 사용됩니다.
        - 비동기 처리를 통해 최대한 빠르게 리스트를 생성합니다.
        - key: API 응답 리스트 각 요소가 딕셔너리인 경우 symbol을 가져올 수 있는 key
            - None인 경우 리스트 요소들로 Symbol객체를 생성합니다.
        - is_valid가 False인 Symbol은 리스트에서 제외됩니다.
        """
        if not _list:  # 빈 객체가 입력될 수 있음 빈 객체면 빈 리스트 반환
            return []

        symbol_generators = [partial(cls, ele[key] if key else ele) for ele in _list]
        symbols = parallel.executor(*symbol_generators).values()
        return [symbol for symbol in symbols if symbol.is_valid]


def search(text: str, limit: int = 15) -> List[Symbol]:
    """
    - api/v3/search
    - text: 검색 문자열
        - 다국어 가능!
    - limit: 검색 결과 갯수 제한 파라미터
    - 검색 결과가 없으면 빈 리스트를 반환합니다.
    """
    en_text = translator(text, to_lang="en")
    req = partial(request, "api/v3/search", limit=limit, cache=True, default=[])
    res = parallel.executor(
        req_en := partial(req, query=en_text),
        req_origin := partial(req, query=text),
    )  # 영어로 번역해서 검색 & 원본 텍스트로 검색
    symbol_codes = {ele["symbol"] for ele in res[req_en] + res[req_origin]}  # 중복 제거
    results = Symbol._from_list(symbol_codes)
    return results


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
    - sector, industry, exchange 매개변수에 대해서는 params속성을 참조하세요
    - country: 국가 코드(ISO 3166-1 alpha-3)
    """

    assert sector is None or sector in cond_search.params["sectors"]
    assert industry is None or industry in cond_search.params["industries"]
    assert exchange is None or exchange in cond_search.params["exchanges"]
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
    return Symbol._from_list(response, key="symbol")


cond_search.params = {
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


def list_gainers() -> List[Symbol]:
    """
    - api/v3/stock_market/gainers
    - 급상승 종목들
    """
    response = request("api/v3/stock_market/gainers")
    return Symbol._from_list(response, key="symbol")


def list_losers() -> List[Symbol]:
    """
    - api/v3/stock_market/losers
    - 급하락 종목들
    """
    response = request("api/v3/stock_market/losers")
    return Symbol._from_list(response, key="symbol")


def list_actives() -> List[Symbol]:
    """
    - api/v3/stock_market/actives
    - 현재 거래량이 가장 많은 종목들
    """
    response = request("api/v3/stock_market/actives")
    return Symbol._from_list(response, key="symbol")


def list_all() -> List[Symbol]:
    """
    - api/v3/stock/list
    - 사용 가능한 모든 symbol 리스트
    - 주의: 4분 이상 소요됨.
    - 리스트 길이: 약 7만개
    """
    response = request("api/v3/stock/list")
    return Symbol._from_list(response, key="symbol")


def list_cot() -> List[Symbol]:
    """api/v4/commitment_of_traders_report/list"""
    response = request("api/v4/commitment_of_traders_report/list")
    return Symbol._from_list(response, key="trading_symbol")


def list_tradable() -> List[Symbol]:
    """
    - api/v3/available-traded/list
    - 주의: 2분 이상 소요됨.
    - 리스트 길이: 약 5만 3천개
    """
    response = request("api/v3/available-traded/list")
    return Symbol._from_list(response, key="symbol")


def list_etf() -> List[Symbol]:
    """api/v3/etf/list"""
    response = request("api/v3/etf/list")
    return Symbol._from_list(response, key="symbol")


def list_sp500() -> List[Symbol]:
    """api/v3/sp500_constituent"""
    response = request("api/v3/sp500_constituent")
    return Symbol._from_list(response, key="symbol")


def list_nasdaq() -> List[Symbol]:
    """api/v3/nasdaq_constituent"""
    response = request("api/v3/nasdaq_constituent")
    return Symbol._from_list(response, key="symbol")


def list_dowjones() -> List[Symbol]:
    """api/v3/dowjones_constituent"""
    response = request("api/v3/dowjones_constituent")
    return Symbol._from_list(response, key="symbol")


def list_index() -> List[Symbol]:
    """api/v3/symbol/available-indexes"""
    response = request("api/v3/symbol/available-indexes")
    return Symbol._from_list(response, key="symbol")


def list_euronext() -> List[Symbol]:
    """api/v3/symbol/available-euronext"""
    response = request("api/v3/symbol/available-euronext")
    return Symbol._from_list(response, key="symbol")


def list_tsx() -> List[Symbol]:
    """api/v3/symbol/available-tsx"""
    response = request("api/v3/symbol/available-tsx")
    return Symbol._from_list(response, key="symbol")


def list_crypto() -> List[Symbol]:
    """api/v3/symbol/available-cryptocurrencies"""
    response = request("api/v3/symbol/available-cryptocurrencies")
    return Symbol._from_list(response, key="symbol")


def list_forex() -> List[Symbol]:
    """api/v3/symbol/available-forex-currency-pairs"""
    response = request("api/v3/symbol/available-forex-currency-pairs")
    return Symbol._from_list(response, key="symbol")


def list_commodity() -> List[Symbol]:
    """api/v3/symbol/available-commodities"""
    response = request("api/v3/symbol/available-commodities")
    return Symbol._from_list(response, key="symbol")
