from collections import defaultdict
from datetime import datetime, date

import wbdata
import numpy as np
import xarray as xr

from compute.scale import standardization
from client.factor import Factor
from client.translate import Multilingual
from config import XARRAY_PATH


def _xr_meta(element, factor, **kwargs) -> dict:
    """World Bank 수집 클라이언트에 대한 Dataset Metadata 생성"""
    return {
        "client": {
            "source": "World Bank API",
            "element": element,
            "factor": factor,
            "collected": datetime.now().strftime("%Y-%m-%d"),
        }
        | kwargs
    }


class DataManager:
    last_loaded = defaultdict(dict)
    loadable = defaultdict(dict)

    def __init__(self, country: str, indicator: str):
        self.country = country
        self.indicator = indicator
        self.zarr_path = XARRAY_PATH / country / f"{indicator}.zarr"
        self.last_loaded = self.__class__.last_loaded[country].get(indicator)
        self.loadable = self.__class__.loadable[country].get(indicator, True)

    def __repr__(self) -> str:
        return f"<DataManager: {self.country} - {self.indicator}>"

    def collect(self) -> xr.DataArray:
        """World Bank에서 데이터를 수집하여 DataArray로 반환합니다."""
        try:
            series = wbdata.get_data(self.indicator, country=self.country, cache=False)
        except RuntimeError:  # World bank 서버의 응답이 잘못되거나 데이터가 없는 경우
            raise ValueError
        t = np.array([np.datetime64(day["date"], "ns") for day in series])
        return xr.DataArray(
            np.array([data["value"] for data in series], dtype=float),
            dims="t",
            coords={"t": t},
            attrs=_xr_meta(element=self.country, factor=self.indicator),
        )

    def loading(self) -> bool:
        """
        - zarr 저장소에 최신 데이터가 존재하도록 합니다.
        - return: 로딩 성공 여부
        """
        today = date.today()
        if self.last_loaded == today:
            return self.loadable

        self.__class__.last_loaded[self.country][self.indicator] = today
        self.last_loaded = today

        try:
            data_array = self.collect()
        except ValueError:
            self.loadable = False
        if np.count_nonzero(~np.isnan(data_array.values)) < 2:
            self.loadable = False
        if not self.loadable:
            self.__class__.loadable[self.country][self.indicator] = False
            return False

        self.zarr_path.parent.mkdir(parents=True, exist_ok=True)
        standardization(data_array).to_zarr(self.zarr_path, mode="w")
        self.__class__.loadable[self.country][self.indicator] = self.loadable = True
        return True

    def get(self, default=None) -> xr.Dataset | None:
        """데이터가 없는 경우 default를 반환합니다."""
        return xr.open_zarr(self.zarr_path) if self.loading() else default


class ClientMeta(type):
    def __new__(meta, name, bases, attrs):
        cls = super().__new__(meta, name, tuple(), dict())
        cls.name = Multilingual(attrs["name"])
        cls.note = Multilingual(attrs["note"])
        cls.indicator_codes = {
            code: name  # 메직 메서드와 name, note를 제외한 모든 속성을 Factor로 간주합니다.
            for name, code in attrs.items()
            if "__" not in name and name not in ["name", "note"]
        }
        cls.__repr__ = lambda ins: f"<{ins.__class__.__name__}: {ins.country}>"
        return cls

    def __call__(cls, country: str):
        ins = super().__call__()
        ins.country = country
        ins.manager = {}
        for code, name in cls.indicator_codes.items():
            manager = DataManager(country, code)
            ins.manager[name] = manager  # DataManager 접근을 위한 통로
            indicator_meta = wbdata.get_indicator(code, cache=True)[0]
            factor = Factor(
                get=manager.get,
                name=indicator_meta["name"],
                note=indicator_meta["sourceNote"],
            )
            setattr(ins, name, factor)
        ins.get = lambda code: getattr(ins, cls.indicator_codes[code]).get()
        return ins
