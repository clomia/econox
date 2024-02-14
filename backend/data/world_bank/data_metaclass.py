import asyncio
from functools import partial
from datetime import datetime, date

import numpy as np
import xarray as xr

from backend.calc import interpolation
from backend.http import WorldBankAPI
from backend.system import EFS_VOLUME_PATH
from backend.data.model import Factor
from backend.data.text import Multilingual
from backend.data.io import xr_open_zarr, xr_to_zarr

DATA_PATH = EFS_VOLUME_PATH / "features/country"


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
    def __init__(self, country: str, indicator: str):
        self.country = country
        self.indicator = indicator
        self.zarr_path = DATA_PATH / country / f"{indicator}.zarr"
        self.api = WorldBankAPI()

    def __repr__(self) -> str:
        return f"<DataManager: {self.country} - {self.indicator}>"

    async def collect(self) -> xr.DataArray | None:
        """World Bank에서 데이터를 수집하여 DataArray로 반환합니다."""
        series = await self.api.get_data(self.indicator, self.country)
        t = np.array([np.datetime64(day["date"], "ns") for day in series])
        return xr.DataArray(
            np.array([data["value"] for data in series], dtype=float),
            dims="t",
            coords={"t": t},
            attrs=_xr_meta(element=self.country, factor=self.indicator),
        )

    async def loading(self):
        """zarr 저장소에 최신 데이터가 존재하도록 합니다."""
        if self.zarr_path.exists():
            array = xr_open_zarr(self.zarr_path)
            collected_attr: str = array.attrs["client"]["collected"]
            collected_date = datetime.strptime(collected_attr, "%Y-%m-%d").date()
            if collected_date == date.today():
                return  # 데이터 갱신 날짜가 오늘이라면 수집할 필요 없음

        data_array = await self.collect()
        if np.count_nonzero(~np.isnan(data_array.values)) < 2:
            return  # 유효한 값 갯수가 2개 미만이면 결측치 취급
        self.zarr_path.parent.mkdir(parents=True, exist_ok=True)
        xr_to_zarr(dataset=interpolation(data_array), path=self.zarr_path)

    async def get(self, default=None) -> xr.Dataset | None:
        """데이터가 없는 경우 default를 반환합니다."""
        await self.loading()  # 데이터가 있다면 반드시 loading후 zarr_path에 데이터가 구축되어있음
        return xr_open_zarr(self.zarr_path) if self.zarr_path.exists() else default


class ClientMeta(type):
    def __new__(meta, name, bases, attrs):
        cls = super().__new__(meta, name, tuple(), dict())
        cls.name = Multilingual(attrs["name"])
        cls.note = Multilingual(attrs["note"])
        cls.indicator_codes = {  # data_class.py 모듈에 작성한 클래스에서 Factor 속성을 긁어옵니다.
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
        ins.load_factor = partial(staticmethod(cls.__class__.load_factor), ins)
        return ins

    async def load_factor(self):
        async def set_factor(indicator, name):
            manager = DataManager(self.country, indicator)
            self.manager[name] = manager  # DataManager 접근을 위한 통로
            indicator_info = await manager.api.get_indicator(indicator)
            factor = Factor(
                get=manager.get,  # Factor 단위 get 함수
                name=indicator_info["name"],
                note=indicator_info["sourceNote"],
            )
            setattr(self, name, factor)

        tasks = [
            set_factor(indicator, name)
            for indicator, name in self.indicator_codes.items()
        ]
        await asyncio.gather(*tasks)
        self.get = lambda code: getattr(self, self.indicator_codes[code]).get()
        return self
