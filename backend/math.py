""" 고성능 수학 연산 모듈 """
from typing import Callable
from datetime import datetime
from calendar import monthrange

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


def marge_lists(*lists, limit) -> list:
    """
    - 리스트들을 받아서 값이 균등하게 포함된 하나의 리스트로 합칩니다.
    - limit[필수]: 결과 리스트 갯수를 제한합니다.
    """
    lengths = [len(lst) for lst in lists]

    base_num = limit // len(lists)  # 각 리스트에서 가져와야 할 기본 요소의 수 계산
    sorted_lists = sorted(  # 남은 요소들을 가져올 리스트를 결정하기 위해 리스트와 그 길이를 함께 정렬
        [(lst, length) for lst, length in zip(lists, lengths)], key=lambda x: -x[1]
    )
    num_from_lists = [base_num for _ in lists]  # 각 리스트에서 가져올 요소의 수를 저장할 변수 초기화

    remaining = limit - sum(num_from_lists)
    for i in range(remaining):  # 남은 요소들을 길이가 큰 리스트부터 차례대로 할당
        while num_from_lists[i % len(lists)] >= sorted_lists[i % len(lists)][1]:
            i += 1
        num_from_lists[i % len(lists)] += 1

    result = []  # 결과 리스트 생성
    for (lst, _), num in zip(sorted_lists, num_from_lists):
        result.extend(lst[:num])

    return result


def calculate_membership_expiry(start: datetime) -> datetime:
    """
    - start: 맴버십 시작일
    - 맴버십 만료일을 계산합니다
    - 다음달 동일 일시를 구하되 마지막 일보다 크면 마지막 일로 대체
    """
    year, month = (
        (start.year + 1, 1) if start.month == 12 else (start.year, start.month + 1)
    )
    day = min(start.day, monthrange(year, month)[1])
    return datetime(year, month, day, start.hour, start.minute, start.second)
