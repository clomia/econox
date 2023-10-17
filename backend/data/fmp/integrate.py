""" 모든 data_class를 Symbol 객체로 통합 """
from __future__ import annotations

import json
import asyncio
from typing import List

import pycountry

from backend.http import FmpAPI
from backend.system import EFS_VOLUME_PATH
from backend.data.fmp import data_metaclass
from backend.data.text import Multilingual, translator

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


class Symbol:
    def __init__(self, code: str):
        """
        - 인스턴스 생성 방법
            - `apple = await Symbol("AAPL").load()`
        - 경고! load 안하면 종목 메타데이터 조회 못함
        """
        self.code = code
        self.info_path = EFS_VOLUME_PATH / "info" / f"symbol/{self.code}.json"
        self.info = {"note": None, "name": None}  # load 메서드가 할당함
        self.is_valid = False  # load 메서드가 할당함

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

    async def load(self):
        self.info = await self.get_info()
        self.is_valid = self.info["name"] and self.info["note"]
        return self

    async def get_info(self):
        """
        - name과 note정보를 수집해서 정제한 뒤 반환합니다.
        - efs-volume에 캐싱을 하여 API 호출을 반복하지 않도록 합니다.
        - api/v3/profile API로 검색하고 정보가 없다면 api/v3/search로 다시 검색합니다.
        """

        # ======= EFS volume 에서 가져오기 =======
        if self.info_path.exists():  # 볼륨에서 가져오기
            return json.load(self.info_path.open("r"))

        # ======= API 사용해서 데이터 수집 =======
        profile_resp, search_api_resp = await asyncio.gather(
            FmpAPI(cache=False).get(f"api/v3/profile/{self.code}"),
            FmpAPI(cache=False).get("api/v3/search", query=self.code),
        )

        name = exchange = currency = description = None
        if profile_resp:
            name = profile_resp[0]["companyName"]
            exchange = profile_resp[0]["exchange"]
            currency = profile_resp[0]["currency"]
            description = profile_resp[0]["description"]
        elif search_api_resp:
            if matched := [
                ele for ele in search_api_resp if ele["symbol"] == self.code
            ]:
                name = matched[0]["name"]
                exchange = matched[0]["stockExchange"]
                currency = matched[0]["currency"]

        # ======= 수집된 데이터 정제 =======
        currency_obj = pycountry.currencies.get(alpha_3=currency) if currency else None
        if name and exchange and currency_obj:  # 이 3가지 정보는 필수
            note_basic = f"{name}({self.code}) is traded at {exchange} and the currency uses {currency_obj.name}. "
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
    async def peers(self) -> List[Symbol]:
        """
        - api/v4/stock_peers
        - 자신과 관련된 Symbol 리스트
        """
        resp = await FmpAPI(cache=True).get("api/v4/stock_peers", symbol=self.code)
        return self._from_list(resp[0]["peersList"]) if resp else []

    @property
    async def current_price(self) -> int | float | None:
        """
        - api/v3/quote
        - 현재 가격
        """
        resp = await FmpAPI(cache=False).get(f"api/v3/quote-short/{self.code}")
        if resp and isinstance(value := resp[0].get("price"), (int, float)):
            return value

    @property
    async def current_volume(self) -> int | float | None:
        """
        - api/v3/quote
        - 현재 거래량
        """
        resp = await FmpAPI(cache=False).get(f"api/v3/quote-short/{self.code}")
        if resp and isinstance(value := resp[0].get("volume"), (int, float)):
            return value

    @property
    async def current_change(self) -> int | float | None:
        """
        - api/v3/quote
        - 현재 가격 변화율 (%)
        """
        resp = await FmpAPI(cache=False).get(f"api/v3/quote/{self.code}")
        if resp and isinstance(value := resp[0].get("changesPercentage"), (int, float)):
            return value


async def search(text: str, limit: int = 8) -> List[Symbol]:
    """
    - api/v3/search
    - text: 검색 문자열
        - 다국어 가능!
    - limit: 검색 결과 갯수 제한
    - 검색 결과가 없으면 빈 리스트를 반환합니다.
    """
    en_text = await translator(text, to_lang="en")
    resp_en, resp_origin = await asyncio.gather(
        FmpAPI(cache=True).get("api/v3/search", limit=limit, query=en_text),
        FmpAPI(cache=True).get("api/v3/search", limit=limit, query=text),
    )
    resp_set = {ele["symbol"] for ele in resp_en + resp_origin}  # 중복 제거

    codes = (  # limit으로 짜르되, 심볼 코드로 검색한 경우라면 해당 심볼은 살리기
        list(resp_set)[: limit - 1] + [target]
        if (target := text.upper()) in resp_set
        else list(resp_set)[:limit]
    )

    symbols = await asyncio.gather(*[Symbol(code).load() for code in codes])

    async def current_volume(symbol):
        return await symbol.current_volume or 0

    # 거래량 기준으로 정렬합니다.
    volume_list = await asyncio.gather(*map(current_volume, symbols))
    volume_map = dict(zip(symbols, volume_list))
    sorted_list = sorted(symbols, key=lambda sym: volume_map[sym], reverse=True)
    for i, sym in enumerate(sorted_list[:]):
        if sym.code == target:
            sorted_list.pop(i)
            sorted_list.insert(0, sym)  # symbol 코드로 검색한 경우 해당 symbol을 맨 앞으로
            break
    return sorted_list


async def cond_search(
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
    resp = await FmpAPI(cache=True).get("api/v3/stock-screener", **params)
    return await asyncio.gather(*(Symbol(ele["symbol"]).load() for ele in resp))


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


async def list_gainers() -> List[Symbol]:
    """
    - api/v3/stock_market/gainers
    - 급상승 종목들
    """
    resp = await FmpAPI(cache=False).get("api/v3/stock_market/gainers")
    return await asyncio.gather(*(Symbol(ele["symbol"]).load() for ele in resp))


async def list_losers() -> List[Symbol]:
    """
    - api/v3/stock_market/losers
    - 급하락 종목들
    """
    resp = await FmpAPI(cache=False).get("api/v3/stock_market/losers")
    return await asyncio.gather(*(Symbol(ele["symbol"]).load() for ele in resp))


async def list_actives() -> List[Symbol]:
    """
    - api/v3/stock_market/actives
    - 현재 거래량이 가장 많은 종목들
    """
    resp = await FmpAPI(cache=False).get("api/v3/stock_market/actives")
    return await asyncio.gather(*(Symbol(ele["symbol"]).load() for ele in resp))


async def list_all() -> List[Symbol]:
    """
    - api/v3/stock/list
    - 사용 가능한 모든 symbol 리스트
    - 주의: 4분 이상 소요됨.
    - 리스트 길이: 약 7만개
    """
    resp = await FmpAPI(cache=True).get("api/v3/stock/list")
    return await asyncio.gather(*(Symbol(ele["symbol"]).load() for ele in resp))


async def list_cot() -> List[Symbol]:
    """api/v4/commitment_of_traders_report/list"""
    resp = await FmpAPI(cache=True).get("api/v4/commitment_of_traders_report/list")
    return await asyncio.gather(*(Symbol(ele["trading_symbol"]).load() for ele in resp))


async def list_tradable() -> List[Symbol]:
    """
    - api/v3/available-traded/list
    - 주의: 2분 이상 소요됨.
    - 리스트 길이: 약 5만 3천개
    """
    resp = await FmpAPI(cache=True).get("api/v3/available-traded/list")
    return await asyncio.gather(*(Symbol(ele["symbol"]).load() for ele in resp))


async def list_etf() -> List[Symbol]:
    """api/v3/etf/list"""
    resp = await FmpAPI(cache=True).get("api/v3/etf/list")
    return await asyncio.gather(*(Symbol(ele["symbol"]).load() for ele in resp))


async def list_sp500() -> List[Symbol]:
    """api/v3/sp500_constituent"""
    resp = await FmpAPI(cache=True).get("api/v3/sp500_constituent")
    return await asyncio.gather(*(Symbol(ele["symbol"]).load() for ele in resp))


async def list_nasdaq() -> List[Symbol]:
    """api/v3/nasdaq_constituent"""
    resp = await FmpAPI(cache=True).get("api/v3/nasdaq_constituent")
    return await asyncio.gather(*(Symbol(ele["symbol"]).load() for ele in resp))


async def list_dowjones() -> List[Symbol]:
    """api/v3/dowjones_constituent"""
    resp = await FmpAPI(cache=True).get("api/v3/dowjones_constituent")
    return await asyncio.gather(*(Symbol(ele["symbol"]).load() for ele in resp))


async def list_index() -> List[Symbol]:
    """api/v3/symbol/available-indexes"""
    resp = await FmpAPI(cache=True).get("api/v3/symbol/available-indexes")
    return await asyncio.gather(*(Symbol(ele["symbol"]).load() for ele in resp))


async def list_euronext() -> List[Symbol]:
    """api/v3/symbol/available-euronext"""
    resp = await FmpAPI(cache=True).get("api/v3/symbol/available-euronext")
    return await asyncio.gather(*(Symbol(ele["symbol"]).load() for ele in resp))


async def list_tsx() -> List[Symbol]:
    """api/v3/symbol/available-tsx"""
    resp = await FmpAPI(cache=True).get("api/v3/symbol/available-tsx")
    return await asyncio.gather(*(Symbol(ele["symbol"]).load() for ele in resp))


async def list_crypto() -> List[Symbol]:
    """api/v3/symbol/available-cryptocurrencies"""
    resp = await FmpAPI(cache=True).get("api/v3/symbol/available-cryptocurrencies")
    return await asyncio.gather(*(Symbol(ele["symbol"]).load() for ele in resp))


async def list_forex() -> List[Symbol]:
    """api/v3/symbol/available-forex-currency-pairs"""
    resp = await FmpAPI(cache=True).get("api/v3/symbol/available-forex-currency-pairs")
    return await asyncio.gather(*(Symbol(ele["symbol"]).load() for ele in resp))


async def list_commodity() -> List[Symbol]:
    """api/v3/symbol/available-commodities"""
    resp = await FmpAPI(cache=True).get("api/v3/symbol/available-commodities")
    return await asyncio.gather(*(Symbol(ele["symbol"]).load() for ele in resp))
