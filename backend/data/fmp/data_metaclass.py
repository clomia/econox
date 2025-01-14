""" 
- data_class.json으로 클라이언트 클래스를 생성하는 메타클래스 모듈 
- FMP의 모든 시계열 데이터 API를 일관된 인터페이스로 제공한다.
"""

import json
from typing import Dict
from pathlib import PosixPath
from functools import partial
from datetime import date, datetime

import numpy as np
import xarray as xr
from httpx import HTTPStatusError

from backend.http import FmpAPI
from backend.calc import interpolation
from backend.data.model import Factor
from backend.data.text import Multilingual
from backend.data.io import xr_open_zarr, xr_to_zarr
from backend.system import ROOT_PATH, EFS_VOLUME_PATH

DATA_PATH = EFS_VOLUME_PATH / "features/symbol"
CLASS_PATH = ROOT_PATH / "backend/data/fmp/data_class.json"


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
        JSON에서 실제 key와 factor값은 둘 다 필요함
        factor는 FMP가 제공하는 camalCase이고 실제 Key는 Python에서 쓸 snake_case이다.
        즉 factor는 config의 key에 대한 실제 API 응답 데이터의 key로 매핑해준다
        """
        try:
            with CLASS_PATH.open(mode="r") as file:
                config = dict(json.load(file))[name]
        except:
            raise NotImplementedError(f"{CLASS_PATH}의 {name} 구성이 정의되지 않음.")
        if not config.get("setting"):
            raise NotImplementedError(
                f"{CLASS_PATH} {name}에 대한 setting가 정의되지 않음."
            )
        for i in meta.mandatory:
            if i not in config["setting"].keys():
                raise NotImplementedError(
                    f"{meta.__name__}의 필수 구성 인자 {i}가 정의되지 않음."
                )
        return config

    def __new__(meta, name, *_args):
        """클래스 생성자"""  # _args 매개변수는 클래스 정적 생성을 위한 호환성 구현입니다.
        config = meta.load_config(name)
        setting = config.pop("setting")

        def get_setting(key: str) -> str | None:
            return setting.get(key, meta.optional.get(key))

        cls = super().__new__(meta, name, tuple(), dict())
        cls.api = get_setting("api")
        cls.api_params = get_setting("params")
        cls.t_key = get_setting("t_key")
        cls.symbol_in_query = bool(get_setting("symbol_in_query"))
        cls.note = Multilingual(text=get_setting("note"))
        cls.name = Multilingual(text=get_setting("name"))
        cls.properties = config  # setting 빼고 나머지는 모두 property임
        cls.factors = {ele["factor"] for ele in config.values()}
        cls.__repr__ = lambda ins: f"<{ins.__class__.__name__}: {ins.symbol}>"
        return cls

    def __call__(cls, symbol: str):
        """인스턴스 생성자"""
        # ========= 기본 속성 구성 =========
        ins = super().__call__()  # 깡통 인스턴스 생성
        ins.symbol = symbol
        ins.path = DATA_PATH / symbol / cls.__name__
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
                get=partial(ins.get, ele["factor"]), name=ele["name"], note=ele["note"]
            )
            setattr(ins, name, factor)
        return ins

    async def collect(self) -> Dict[str, xr.DataArray]:
        """
        - 모든 펙터에 대한 시계열 데이터를 수집한 뒤 딕셔너리로 매핑해서 반환합니다.
        - FMP 서버 응답이 잘못된 경우 raise HTTPStatusError
        - 데이터가 전혀 없는 경우 raise ValueError
        - 누락된 데이터는 np.nan으로 대체됩니다.
        """
        series: list = await FmpAPI(cache=False).get(self.api, **self.api_params)
        if not series:  # 데이터가 없는 경우 ValueError
            raise ValueError(
                f"FMP에 {self.symbol} symbol에 대한 데이터가 존재하지 않습니다."
            )
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

    async def loading(self):
        """zarr 저장소에 최신 데이터가 존재하도록 합니다."""

        for fac in self.factors:  # 데이터 갱신 여부 확인
            if self.zarr_path(fac).exists():
                array = xr_open_zarr(self.zarr_path(fac))
                collected_date = datetime.strptime(
                    array.attrs["client"]["collected"], "%Y-%m-%d"
                ).date()
                if collected_date == date.today():
                    return  # 데이터 갱신 필요 없음
        try:
            collected = await self.collect()
        except (HTTPStatusError, ValueError):
            return  # 데이터를 가져올 수 없거나 데이터가 비었으면 아무것도 안함

        self.path.mkdir(parents=True, exist_ok=True)
        for factor, data_array in collected.items():
            if np.count_nonzero(~np.isnan(data_array.values)) < 2:
                continue  # 유효한 값 갯수가 2개 미만이면 결측 factor로 취급
            xr_to_zarr(dataset=interpolation(data_array), path=self.zarr_path(factor))

    async def get(self, factor: str, default=None) -> xr.Dataset | None:
        """factor Dataset을 반환합니다. 데이터가 없는 경우 default를 반환합니다."""
        assert factor in self.factors  # JSON에 정의되지 않은 Factor입니다.
        await self.loading()
        return (
            xr_open_zarr(self.zarr_path(factor))
            if self.zarr_path(factor).exists()
            else default
        )


class HistoricalPriceFullMeta(ClientMeta):
    """api/v3/historical-price-full API 전용 클라이언트"""

    async def collect(self):  # collect 메서드 재정의
        # FMP 서버는 안정적인 응답 시간을 위해 from 인자가 없다면 기본적으로 5년 전까지의 데이터만 수신합니다.
        # from 인자로 "1900-01-01" 를 넣어서 모든 데이터를 가져올 수 있습니다.(이렇게 하라고 FMP한테 확인받음)
        data: dict = await FmpAPI(cache=False).get(
            path=self.api, **self.api_params | {"from": "1900-01-01"}
        )

        # 값이 historical 안에 들어있으며, 값이 없으면 historical 키도 없음
        if not (series := data.get("historical")):
            raise ValueError(
                f"FMP에 {self.symbol} symbol에 대한 데이터가 존재하지 않습니다."
            )

        # 나머지는 부모클래스 코드와 동일
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
