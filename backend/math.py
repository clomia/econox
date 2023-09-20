""" 고성능 수학 연산 모듈 """
import math
from typing import Callable
from datetime import datetime, timezone, timedelta

import pytz
import numpy as np
import xarray as xr
from scipy.interpolate import PchipInterpolator

from backend.system import MEMBERSHIP


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


def marge_lists(*lists: list, limit: int) -> list:
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


def utcstr2datetime(timestring: str) -> datetime:
    """UTC 시간대 ISO 8601 문자열 -> Asia/Seoul 시간대 datetime 객체"""
    utc_time = datetime.fromisoformat(
        timestring.replace("Z", "+00:00"),
    ).astimezone(pytz.utc)
    return utc_time.astimezone(pytz.timezone("Asia/Seoul"))


def datetime2utcstr(dt: datetime) -> str:
    """Asia/Seoul 시간대 datetime 객체 -> UTC 시간대 ISO 8601 문자열"""
    utc_datetime = dt - timedelta(hours=9)
    return utc_datetime.strftime("%Y-%m-%dT%H:%M:%S.000Z")


def calc_next_billing_date(base: datetime, current: datetime) -> datetime:
    """
    - 다음 청구 날짜 계산
    - PayPal에서 사용하는 알고리즘과 동일합니다.
    - 맴버십 변경 시에는 next_billing_date_adjust_membership_change 함수를 사용하세요.
    - base: 기준 청구일시
    - current: 최근 청구 날짜
    - return: 다음 청구 날짜
    """
    year, month, day = current.year, current.month, base.day

    def is_leap_year(year):  # 윤년인지 아닌지 판별하는 함수
        return (year % 4 == 0 and year % 100 != 0) or (year % 400 == 0)

    next_month = month + 1 if month != 12 else 1
    year += 1 if month == 12 else 0

    # 모든 달의 일수가 같지 않고 윤년과 평년이 있다는 점을 고려하여 계산
    if day == 31:
        if next_month in [4, 6, 9, 11]:
            day = 30
        elif next_month == 2:
            if is_leap_year(year):
                day = 29
            else:
                day = 28
    elif day == 30 and next_month == 2:
        if is_leap_year(year):
            day = 29
        else:
            day = 28
    elif day == 29 and next_month == 2 and not is_leap_year(year):
        day = 28

    return datetime(year, next_month, day, base.hour, base.minute, base.second)


def calc_next_billing_date_adjust_membership_change(
    base_billing: datetime,
    current_billing: datetime,
    current_membership: str,
    new_membership: str,
    change_day: datetime,
    currency: str,
) -> datetime:
    """
    - 맴버십 변경에 따른 차액이 적용된 다음 결제일을 계산합니다.
    - 변경된 맴버십을 되돌리는 경우의 다음 결제일은 next_billing_date 함수를 사용하세요.
        - 이 함수는 맴버십 변경 여부를 알 수 없으므로 역산이 성립되지 않습니다.
    - base_billing: 기준 청구일
    - current_billing: 현재 맴버십 청구 날짜
    - current_membership: 현재 맴버십
    - new_membership: 변경할 맴버십
    - change_day: 맴버십 변경 날짜
    - return: 다음 청구 날짜
    """

    default_next_billing = calc_next_billing_date(base_billing, current_billing)

    membership_days = (default_next_billing - current_billing).days
    current_daily_amount = MEMBERSHIP[current_membership][currency] / membership_days
    new_daily_amount = MEMBERSHIP[new_membership][currency] / membership_days

    remaining_days = (default_next_billing - change_day).days
    remaining_amount = remaining_days * current_daily_amount

    new_remaining_days = math.floor(remaining_amount / new_daily_amount)
    return change_day + timedelta(days=new_remaining_days)
