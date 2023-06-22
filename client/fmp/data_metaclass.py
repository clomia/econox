""" 
- data_class.json으로 클라이언트 클래스를 생성하는 메타클래스 모듈 
- FMP의 모든 시계열 데이터 API를 일관된 인터페이스로 제공한다.
"""

import os
import json
from datetime import date, datetime
from functools import partial
from pathlib import PosixPath
from typing import Dict
from collections import defaultdict

import requests
import numpy as np
import xarray as xr

from compute.scale import standardization
from client.factor import Factor
from client.translate import Multilingual
from config import ROOT_PATH, XARRAY_PATH

API_KEY = os.getenv("FMP_API_KEY")
HOST = "https://financialmodelingprep.com"
CLASS_PATH = ROOT_PATH / "client" / "fmp" / "data_class.json"


def _xr_meta(element, factor, **kwargs) -> dict:
    """FMP 수집 클라이언트에 대한 Dataset Metadata 생성"""
    return {
        "client": {
            "source": "Financial Modeling Prep API",
            "element": element,
            "factor": factor,
            "collected": datetime.now().strftime("%Y-%m-%d"),
        }
        | kwargs
    }


class ClientMeta(type):
    # JSON setting에서 선택 키에 대한 기본값과 필수 키 정의
    mandatory = ["api", "note"]
    optional = {"params": {}, "symbol_in_query": False, "t_key": "date"}

    @classmethod
    def load_config(meta, name) -> dict:
        """
        - JSON에서 클래스 구성을 불러옵니다.
        - JSON 구성이 올바른지 검사합니다.
        """
        try:
            config = dict(json.load(CLASS_PATH.open(mode="rb")))[name]
        except:
            raise NotImplementedError(f"{CLASS_PATH}의 {name} 구성이 정의되지 않음.")
        if not config.get("setting"):
            raise NotImplementedError(f"{CLASS_PATH} {name}에 대한 setting가 정의되지 않음.")
        for i in meta.mandatory:
            if i not in config["setting"].keys():
                raise NotImplementedError(f"{meta.__name__}의 필수 구성 인자 {i}가 정의되지 않음.")
        return config

    def __new__(meta, name, *_args):
        """클래스 생성자"""  # _args 매개변수는 클래스 정적 생성을 위한 호환성 구현입니다.
        config = meta.load_config(name)
        setting = config.pop("setting")

        def get_setting(key: str) -> str | None:
            return setting.get(key, meta.optional.get(key))

        cls = super().__new__(meta, name, tuple(), dict())
        cls.api = f"{HOST}/{get_setting('api')}"
        cls.api_params = {"apikey": API_KEY} | get_setting("params")
        cls.t_key = get_setting("t_key")
        cls.symbol_in_query = bool(get_setting("symbol_in_query"))
        cls.note = Multilingual(text=get_setting("note"))
        cls.name = Multilingual(text=get_setting("name"))
        cls.properties = config  # setting 빼고 나머지는 모두 property임
        cls.factors = {ele["factor"] for ele in config.values()}
        cls.__repr__ = lambda ins: f"<{ins.__class__.__name__}: {ins.symbol}>"
        # ========= 동적 속성 구성 =========
        cls.last_loaded = {}
        cls.missing_factors = defaultdict(set)
        return cls

    def __call__(cls, symbol: str):
        """인스턴스 생성자"""
        # ========= 기본 속성 구성 =========
        ins = super().__call__()  # 깡통 인스턴스 생성
        ins.symbol = symbol
        ins.path = XARRAY_PATH / cls.__name__ / symbol
        ins.last_loaded = cls.last_loaded.get(symbol)
        ins.missing_factors = cls.missing_factors[symbol]  # set 레퍼런스
        if cls.symbol_in_query:  # symbol을 쿼리스트링으로 넣기
            ins.api_params = cls.api_params | {"symbol": symbol}
        else:  # symbol을 URL경로로 넣기
            ins.api = f"{cls.api}/{symbol}"
        # ========= 메서드 구성 =========
        # self 인자로 인스턴스가 주입되도록 함수 객체를 변경
        ins.collect = partial(staticmethod(cls.__class__.collect), ins)
        ins.zarr_path = partial(staticmethod(cls.__class__.zarr_path), ins)
        ins.loading = partial(staticmethod(cls.__class__.loading), ins)
        ins.get = partial(staticmethod(cls.__class__.get), ins)
        # ========= Factor 구성 =========
        for name, ele in cls.properties.items():
            factor = Factor(
                get=partial(ins.get, ele["factor"]),
                name=ele["name"],
                note=ele["note"],
            )
            setattr(ins, name, factor)
        return ins

    def collect(self) -> Dict[str, xr.DataArray]:
        """
        - 모든 펙터에 대한 시계열 데이터를 수집한 뒤 딕셔너리로 매핑해서 반환합니다.
        - FMP 서버 응답이 잘못된 경우 raise HTTPError
        - 데이터가 전혀 없는 경우 raise ValueError
        - 누락된 데이터는 np.nan으로 대체됩니다.
        """
        response = requests.get(self.api, params=self.api_params)
        response.raise_for_status()  # FMP 서버의 응답이 잘못된 경우 HTTPError
        if not (series := response.json()):  # 데이터가 없는 경우 ValueError
            raise ValueError(f"FMP에 {self.symbol} symbol에 대한 데이터가 존재하지 않습니다.")

        t = np.array([np.datetime64(day[self.t_key], "ns") for day in series])
        collected = {}
        for factor in self.factors:
            collected[factor] = xr.DataArray(
                np.array([day.get(factor, np.nan) for day in series], dtype=float),
                dims="t",
                coords={"t": t},
                attrs=_xr_meta(element=self.symbol, factor=factor),
            )

        return collected

    def zarr_path(self, factor: str) -> PosixPath:
        """
        - factor에 대한 zarr 경로를 반환합니다.
        - 로직상 factor에 대한 경로를 만들어주는거지 해당 경로에 있다는건 아님
        """
        assert factor in self.factors  # use_factors.json를 확인해주세요
        return self.path / f"{factor}.zarr"

    def loading(self) -> list:
        """
        - zarr 저장소에 최신 데이터가 존재하도록 합니다.
        - return: 로딩된 factor set
            - 수집되지 않은 factor는 set에서 제외됩니다.
        """
        today = date.today()
        if self.last_loaded == today:  # do nothing
            return self.factors - self.missing_factors

        self.__class__.last_loaded[self.symbol] = self.last_loaded = today

        try:
            collected = self.collect()
        except (requests.HTTPError, ValueError):
            self.missing_factors.update(self.factors)
            return self.factors - self.missing_factors  # -> set()

        # 업데이트(덮어쓰기)하는 경우 디렉토리가 이미 존재함
        self.path.mkdir(parents=True, exist_ok=True)

        for factor, data_array in collected.items():
            if np.count_nonzero(~np.isnan(data_array.values)) < 2:
                # nan이 아닌 값 갯수가 2개 미만이면 결측 factor로 취급
                self.missing_factors.add(factor)
                continue
            standardization(data_array).to_zarr(self.zarr_path(factor), mode="w")
        return self.factors - self.missing_factors

    def get(self, factor: str, default=None) -> xr.Dataset | None:
        """factor Dataset을 반환합니다. 데이터가 없는 경우 default를 반환합니다."""
        assert factor in self.factors  # JSON에 정의되지 않은 Factor입니다.
        factors = self.loading()
        if factor not in factors:  # 결측된 factor
            return default
        return xr.open_zarr(self.zarr_path(factor))


class SingleClientMeta(ClientMeta):
    """Symbol 인자를 받지 않는 ClientMeta"""

    def __call__(cls):  # symbol 인자 안받도록 재정의
        ins = super().__call__(symbol="no_symbol")
        ins.api = cls.api  # symbol이 없어서 ins.api가 cls.api임
        return ins


class HistoricalPriceFullMeta(ClientMeta):
    """api/v3/historical-price-full API 전용 클라이언트"""

    def collect(self):  # collect 메서드 재정의
        response = requests.get(self.api, params=self.api_params)
        response.raise_for_status()

        # 재정의 부분: 값이 historical 안에 들어있으며, 값이 없으면 historical 키도 없음
        if not (series := dict(response.json()).get("historical")):
            raise ValueError(f"FMP에 {self.symbol} symbol에 대한 데이터가 존재하지 않습니다.")

        t = np.array([np.datetime64(day[self.t_key], "ns") for day in series])
        collected = {}

        for factor in self.factors:
            collected[factor] = xr.DataArray(
                np.array([day[factor] for day in series], dtype=float),
                dims="t",
                coords={"t": t},
                attrs=_xr_meta(element=self.symbol, factor=factor),
            )

        return collected


class UsaEconomicIndicatorMeta(ClientMeta):
    """
    - Economic Indicator API 전용 클라이언트
    - 인스턴스를 대표하는 value Factor를 가진다.
        - 이 구현을 위해 JSON에서 property이름이 API factor이름과 같아야 한다.
    """

    def __new__(meta, name, *_args):
        cls = super().__new__(meta, name, *_args)
        cls.factors.add("value")
        return cls

    def __call__(cls, indicator: str):  # symbol 말고 name을 사용하도록 재정의
        ins = super().__call__(symbol=indicator)
        ins.api_params = cls.api_params | {"name": indicator}  # -> collect 메서드에서 사용
        factor = Factor(
            get=partial(ins.get, "value"),
            name=cls.properties[indicator]["name"],
            note=cls.properties[indicator]["note"],
        )
        setattr(ins, "value", factor)
        return ins
