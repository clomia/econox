from typing import Callable

import numpy as np
import xarray as xr
from scipy.interpolate import PchipInterpolator


def standardization(
    data: xr.DataArray, *, interpolator: Callable = PchipInterpolator
) -> xr.Dataset:
    """
    - 시계열 데이터를 0~1 사이의 scale을 가지며 연속적인 일별 데이터로 변환합니다.
    - data: 시간 t에 대한 값 x를 가지는 DataArrray
        - 결측치 있어도 됌, 정렬 되어있지 않아도 됌, 동일한 날짜 여러개 있어도 됌
    - interpolator: scipy.interpolate 함수 (default: PchipInterpolator)
        - from scipy.interpolate import PchipInterpolator, Akima1DInterpolator
        - PchipInterpolator: 변동성이 적은 경우에 추천
        - Akima1DInterpolator: 변동성이 큰 경우에 추천
    - return: t축을 공유하는 DataArray 2개(daily, mask)가 있는 Dataset
        - daily: 연속화된 시계열 데이터
        - mask: 해당 t축에 할당된 값이 원본이면 True인 bool Array
        - 입력된 DataArray의 attrs를 보존합니다.
    """
    # compute() 되지 않은 dask Array인 경우 엄청 오래걸립니다. 무조건 모두 메모리로 불러와야 함.
    cleansed = data.compute().drop_duplicates("t").dropna(dim="t").sortby("t")
    interp = interpolator(cleansed.t.values.astype(float), cleansed.values)
    daily_t = np.arange(  # 연속적인 일단위 t축을 다시 구성함
        start=cleansed.t.values[0],
        stop=cleansed.t.values[-1] + np.timedelta64(1, "D"),
        step=np.timedelta64(1, "D"),
    )
    daily_x: np.ndarray = interp(daily_t.astype(float))
    min_x, max_x = daily_x.min(), daily_x.max()
    if min_x != max_x:  # Min-Max Scaling
        scaled_daily_x = (daily_x - min_x) / (max_x - min_x)
    else:  # 모든 값이 같다면 모두 0.5로 변환
        scaled_daily_x = np.full(daily_x.shape, 0.5)

    daily = xr.DataArray(scaled_daily_x, dims=("t"), coords={"t": daily_t})
    mask = ~cleansed.reindex(t=daily.t).isnull()  # 원본 값 찾기용
    metadata = {
        "standardization": {
            "interpolation": {
                "method": interpolator.__name__,
                "ratio": 1 - float(mask.mean()),  # 보간된 값의 비율
            },
            "scaling": {"origin_min": min_x, "origin_max": max_x},
        }
    }
    return xr.Dataset(
        {"daily": daily, "mask": mask},
        attrs=data.attrs | metadata,  # 원본 메타데이터 보존
    )


def destandardize(standardized: xr.Dataset) -> xr.DataArray:
    """
    - standardization의 역함수
    - standardized: standardization 함수에서 반환된 Dataset
    - return: 원본 DataArray
        - 불가피하게 미세한 실수 오차가 발생합니다.
    - 원본 데이터가 일단위보다 작은 해상도를 가질 경우 복원이 불가능합니다.
    """
    dataset = standardized.compute()
    origin_min = dataset.attrs["standardization"]["scaling"]["origin_min"]
    origin_max = dataset.attrs["standardization"]["scaling"]["origin_max"]
    origin_x = dataset.daily[dataset.mask]
    restored = origin_x * (origin_max - origin_min) + origin_min
    return restored
