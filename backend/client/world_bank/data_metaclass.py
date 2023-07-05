from datetime import datetime, date
from functools import lru_cache, partial

import wbdata  #! wbdata 라이브러리의 캐싱 알고리즘은 thread-safe하지 않으므로 항상 cache=False 해줘야 한다!
import numpy as np
import xarray as xr

from backend.compute import parallel
from backend.compute.scale import standardization
from backend.client.factor import Factor
from backend.client.translate import Multilingual
from backend.system import XARRAY_PATH, LRU_CACHE_SIZE


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
        self.zarr_path = XARRAY_PATH / country / f"{indicator}.zarr"

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

    def loading(self):
        """zarr 저장소에 최신 데이터가 존재하도록 합니다."""
        if self.zarr_path.exists():
            array = xr.open_zarr(self.zarr_path)
            collected_date = datetime.strptime(
                array.attrs["client"]["collected"], "%Y-%m-%d"
            ).date()  # 데이터 갱신 여부 확인
            if collected_date == date.today():
                return  # 수집할 필요 없음
        try:
            data_array = self.collect()
        except ValueError:
            return  # 데이터가 전혀 없음.
        if np.count_nonzero(~np.isnan(data_array.values)) < 2:
            return  # 데이터에 값이 2개 미만임
        self.zarr_path.parent.mkdir(parents=True, exist_ok=True)
        standardization(data_array).to_zarr(self.zarr_path, mode="w")

    def get(self, default=None) -> xr.Dataset | None:
        """데이터가 없는 경우 default를 반환합니다."""
        self.loading()
        return xr.open_zarr(self.zarr_path) if self.zarr_path.exists() else default


@lru_cache(maxsize=LRU_CACHE_SIZE)
def get_indicator(indicator):  # wbdata cache 알고리즘 말고 쓰레드 안전한 lru_cache 사용
    """지표에 대한 메타데이터 불러오기"""
    return wbdata.get_indicator(indicator, cache=False)[0]


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

        def _set_factor(indicator, name):
            """
            - ins 객체에 indicator Factor를 name 속성으로 할당합니다.
            - indicator: Factor에 대한 world bank 지표 코드
            - get_indicator 사용하기 때문에 무조건 비동기로 실행되어야 하는 함수입니다.
            """
            manager = DataManager(country, indicator)
            ins.manager[name] = manager  # DataManager 접근을 위한 통로
            indicator_meta = get_indicator(indicator)
            factor = Factor(
                get=manager.get,
                name=indicator_meta["name"],
                note=indicator_meta["sourceNote"],
            )
            setattr(ins, name, factor)

        set_factor_functions = [
            partial(_set_factor, indicator, name)
            for indicator, name in cls.indicator_codes.items()
        ]  # 대량의 get_indicator 호출을 모두 비동기로 처리
        parallel.executor(*set_factor_functions)
        ins.get = lambda code: getattr(ins, cls.indicator_codes[code]).get()
        return ins
