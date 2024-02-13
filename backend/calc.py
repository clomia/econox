""" 고성능 수학 연산 모듈 """

import math
from typing import Callable
from itertools import permutations, combinations
from datetime import datetime, timedelta

import pytz
import numpy as np
import xarray as xr
from numpy.typing import NDArray
from pydantic import constr
from scipy.interpolate import PchipInterpolator
from statsmodels.tsa.stattools import grangercausalitytests, coint

from backend.system import MEMBERSHIP, LogSuppressor


def normalize(
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
        "normalize": {
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


def restore_scale(normalized: xr.Dataset) -> xr.DataArray:
    """
    - normalize 데이터에서 Min-Max Scale만 복원
    - normalized: normalize 함수에서 반환된 Dataset
    - return: 스케일이 복원된 daily DataArray
    """
    dataset = normalized.compute()
    origin_min = dataset.attrs["normalize"]["scaling"]["origin_min"]
    origin_max = dataset.attrs["normalize"]["scaling"]["origin_max"]
    return dataset.daily * (origin_max - origin_min) + origin_min


def denormalize(normalized: xr.Dataset) -> xr.DataArray:
    """
    - normalize의 역함수
    - normalized: normalize 함수에서 반환된 Dataset
    - return: 원본 DataArray
        - 불가피하게 미세한 실수 오차가 발생합니다.
    - 원본 데이터가 일단위보다 작은 해상도를 가질 경우 복원이 불가능합니다.
    """
    dataset = normalized.compute()
    restored_scale = restore_scale(dataset)
    return restored_scale[dataset.mask]


def marge_lists(*lists: list, limit: int) -> list:
    """
    여러 리스트들을 받아 limit에 지정된 수만큼의 요소를 포함하도록
    각 리스트에서 균등하게 아이템을 선택하여 하나의 리스트로 합칩니다.
    """
    # 각 리스트의 길이를 계산
    lengths = [len(lst) for lst in lists]

    # 리스트와 그 길이를 쌍으로 묶어서 길이에 따라 내림차순으로 정렬
    paired_lists = sorted(zip(lists, lengths), key=lambda x: x[1], reverse=True)

    # 각 리스트에서 선택할 아이템의 수를 저장할 변수 초기화
    num_from_lists = [0 for _ in lists]

    # 선택된 아이템의 총 수
    count = 0
    # 아직 선택할 아이템이 남아있고, limit에 도달하지 않았다면 계속 선택
    while count < limit and any(
        x[1] > num_from_lists[i] for i, x in enumerate(paired_lists)
    ):
        for i, (lst, length) in enumerate(paired_lists):
            if count < limit and length > num_from_lists[i]:
                num_from_lists[i] += 1
                count += 1

    # 결과 리스트 생성
    result = []
    for (lst, _), num in zip(paired_lists, num_from_lists):
        result.extend(lst[:num])

    return result


# Dockerfile 보면 컨테이너에 시간대를 Asia/Seoul 로 박아놨다.
# 따라서 Asia/Seoul 시간대가 곧 서버 시간대이다. 이건 계속 유지한다.
def utcstr2datetime(timestring: str) -> datetime:
    """UTC 시간대 ISO 8601 문자열 -> Asia/Seoul 시간대 datetime 객체"""
    utc_time = datetime.fromisoformat(
        timestring.replace("Z", "+00:00"),
    ).astimezone(pytz.utc)
    return utc_time.astimezone(pytz.timezone("Asia/Seoul"))


utcstr_type = constr(pattern=r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.000Z$")


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


class PairwiseAnalyzer:
    def __init__(self, xt: NDArray, yt: NDArray):
        self.xt = xt
        self.yt = yt

    @staticmethod
    def _interpret_p_value(p_value):
        """
        - p_value가 0.05보다 큰 경우 기각합니다. 0을 반환합니다.
        - p_value가 0.05보다 작은 경우 0에서 1사이의 역수로 변환해 반환합니다.
            - 1에 가까울수록 긍정, 0에 가까울수록 부정입니다.
        """
        if p_value >= 0.05:  # p-value가 0.05 이상인 경우, 기각
            return 0
        else:  # p-value가 0.05 미만인 경우, 0에서 1 사이의 역수로 표현
            return (0.05 - p_value) / 0.05

    @staticmethod
    def _gen_lags_list(data_length, total_lags=10):
        """
        - 그레인저 인과관계 계산에 사용될 lags 리스트를 생성합니다.
        - 최대 lag는 30과 data_length/5 중 작은 값입니다.
            - 계산 함수에서 lag가 데이터 길이의 20% 이상인 경우 잘못된 lag라는 에러가 발생하기 때문
        - 리스트는 최대 total_lags 길이를 가지며 최대한 동일한 간격인 lag들을 가집니다.
        """
        max_lags = 30

        # 가능한 최대 lags 계산
        possible_lag = min(data_length // 5, max_lags)

        # 균일한 간격으로 lags 리스트 생성
        if possible_lag >= total_lags:
            step = max(1, (possible_lag - 1) // (total_lags - 1))
            lags = [v for i in range(total_lags) if (v := 1 + i * step) <= possible_lag]
        else:
            lags = list(range(1, possible_lag + 1))

        if not lags:
            raise ValueError(
                "[grangercausality] 대상 시계열 길이가 너무 짧아 계산을 수행할 수 없습니다."
            )
        return lags

    def grangercausality(self):
        """
        - 선후관계 정도 계산
        - xt가 yt에 선행하는 정도를 계산해서 0에서 1사이의 값을 반환합니다.
        """
        data = np.column_stack([self.xt, self.yt])
        lags = self._gen_lags_list(data.shape[0])

        with LogSuppressor():
            # verbose가 deprecated임에도, False로 설정하지 않으면 내부적으로 verbose=True가 됌
            # 이후 statsmodels 버전 업데이트 시 verbose 매개변수 제거하고 로그 출력 억제하는 법 알아봐야 함
            result = grangercausalitytests(
                data, maxlag=lags, addconst=True, verbose=False
            )

        # 여러 검정 결과의 p-value를 저장할 리스트
        all_p_values = []

        # 각 lag에 대한 검정 결과를 순회하며 p-value를 수집합니다.
        for lag, result in result.items():
            for test in result[0].values():
                # 각 검정의 p-value를 리스트에 추가합니다.
                all_p_values.append(test[1])

        # 모든 p-value의 평균을 계산합니다.
        avg_p_value = np.mean(all_p_values)
        return self._interpret_p_value(avg_p_value)

    def cointegration(self) -> float:
        """
        - 유사한 정도 계산
        - 공적분 관계의 강도를 나타내는 0에서 1 사이의 값을 반환합니다.
        """
        # 시계열 데이터는 대부분 추세가 있으므로 ct를 사용합니다.
        _, p_value, _ = coint(self.xt, self.yt)
        return self._interpret_p_value(p_value)


class MultivariateAnalyzer:
    """
    - 다변량 시계열 관계 분석기
    - 시계열은 dataset의 변수명으로 구분합니다.
    """

    def __init__(self, dataset: xr.Dataset):
        self.dataset = dataset
        self.perm_pairs = list(permutations(self.dataset.data_vars, 2))
        self.comb_pairs = list(combinations(self.dataset.data_vars, 2))

    def grangercausality(self):
        result = {}
        for pair in self.perm_pairs:
            value = PairwiseAnalyzer(
                xt=self.dataset[pair[0]].values,
                yt=self.dataset[pair[1]].values,
            ).grangercausality()
            if value:
                result[pair] = value
        return result

    def cointegration(self):
        result = {}
        for pair in self.comb_pairs:
            value = PairwiseAnalyzer(
                xt=self.dataset[pair[0]].values, yt=self.dataset[pair[1]].values
            ).cointegration()
            if value:
                result[pair] = value
        return result  # 공적분은 순서 안중요함
