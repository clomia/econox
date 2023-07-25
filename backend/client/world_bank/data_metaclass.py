from datetime import datetime, date
from functools import lru_cache, partial

import wbdata
import numpy as np
import xarray as xr

from backend.compute import parallel, standardization
from backend.system import XARRAY_PATH
from backend.client.factor import Factor
from backend.client.translate import Multilingual


def wbdata_safe_caller(wb_func):
    """
    - wbdata 함수가 안전하게 작동하도록 감쌉니다.
    - wbdata 라이브러리의 캐싱 알고리즘은 thread-safe하지 않으므로
    항상 cache=False 해줘야 하며, 결과가 없을 때 RuntimeError를 발생시키는데
    에러를 발생시키는 대신에 빈 리스트를 반환하도록 변경합니다.
    """

    def wrapper(*args, **kwargs):
        try:
            return wb_func(*args, **kwargs, cache=False)
        except RuntimeError:
            return []

    return wrapper


get_data = wbdata_safe_caller(wbdata.get_data)


@lru_cache(maxsize=1024)
def get_indicator(indicator):  # 이건 캐싱이 필요해서 @lru_cache 사용하는 함수로 재정의
    _get_indicator = wbdata_safe_caller(wbdata.get_indicator)
    return _get_indicator(indicator)[0]


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

    def collect(self) -> xr.DataArray | None:
        """World Bank에서 데이터를 수집하여 DataArray로 반환합니다."""
        series = get_data(self.indicator, country=self.country)
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
            collected_attr: str = array.attrs["client"]["collected"]
            collected_date = datetime.strptime(collected_attr, "%Y-%m-%d").date()
            if collected_date == date.today():
                return  # 데이터 갱신 날짜가 오늘이라면 수집할 필요 없음

        data_array = self.collect()
        if np.count_nonzero(~np.isnan(data_array.values)) < 2:
            return  # 유효한 값 갯수가 2개 미만이면 결측치 취급
        self.zarr_path.parent.mkdir(parents=True, exist_ok=True)
        standardization(data_array).to_zarr(self.zarr_path, mode="w")

    def get(self, default=None) -> xr.Dataset | None:
        """데이터가 없는 경우 default를 반환합니다."""
        self.loading()  # 데이터가 있다면 반드시 loading후 zarr_path에 데이터가 구축되어있음
        return xr.open_zarr(self.zarr_path) if self.zarr_path.exists() else default


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

        def _set_factor(indicator, name):
            """
            - ins 객체에 indicator Factor를 name 속성으로 할당합니다.
            - indicator: Factor에 대한 world bank 지표 코드
            - get_indicator 사용하기 때문에 무조건 병렬로 실행되어야 하는 함수입니다.
            """
            manager = DataManager(country, indicator)
            ins.manager[name] = manager  # DataManager 접근을 위한 통로
            indicator_meta = get_indicator(indicator)
            factor = Factor(
                get=manager.get,  # Factor 단위 get 함수
                name=indicator_meta["name"],
                note=indicator_meta["sourceNote"],
            )
            setattr(ins, name, factor)

        factor_properties_setup = [
            partial(_set_factor, indicator, name)
            for indicator, name in cls.indicator_codes.items()
        ]  # 대량의 get_indicator 호출을 모두 병렬로 처리
        parallel.executor(*factor_properties_setup)

        # 인스턴스단위 get함수
        ins.get = lambda code: getattr(ins, cls.indicator_codes[code]).get()
        return ins
