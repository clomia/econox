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


def interpolation(data: xr.DataArray, *, interpolator: Callable = PchipInterpolator):
    """
    - 시계열 데이터를 연속적인 일별 데이터로 보간합니다.
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
    daily = xr.DataArray(daily_x, dims=("t"), coords={"t": daily_t})
    mask = ~cleansed.reindex(t=daily.t).isnull()  # 원본 값 찾기용
    metadata = {
        "normalize": {
            "interpolation": {
                "method": interpolator.__name__,
                "ratio": 1 - float(mask.mean()),  # 보간된 값의 비율
            },
        }
    }
    return xr.Dataset(
        {"daily": daily, "mask": mask},
        attrs=data.attrs | metadata,  # 원본 메타데이터 보존
    )


def deinterpolate(dataset: xr.Dataset) -> xr.DataArray:
    """
    - interpolation의 역함수
    - dataset: interpolation의 함수에서 반환된 Dataset
    - return: 원본 DataArray
        - 불가피하게 미세한 실수 오차가 발생합니다.
    - 원본 데이터가 일단위보다 작은 해상도를 가질 경우 복원이 불가능합니다.
    """
    ds = dataset.compute()
    return ds.daily[ds.mask]


def scaling(arr: NDArray | xr.DataArray) -> NDArray | xr.DataArray:
    """
    - 시계열 데이터를 0~1 사이의 scale을 가지는 데이터로 변환합니다.
    - Numpy Array, DataArray 모두 처리 가능합니다.
    """
    min_x, max_x = arr.min(), arr.max()
    scaled_data = (  # 모든 값이 같다면 모두 0.5로 변환
        (arr - min_x) / (max_x - min_x) if min_x != max_x else np.full(arr.shape, 0.5)
    )
    # 입력이 xarray.DataArray인 경우, 결과도 DataArray로 반환
    return arr.copy(data=scaled_data) if isinstance(arr, xr.DataArray) else scaled_data


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
    def _gen_lags_list(data_length, total_lags=5):
        """
        - 그레인저 인과관계 계산에 사용될 lags 리스트를 생성합니다.
        - 최대 lag는 30과 data_length/5 중 작은 값입니다.
            - 계산 함수에서 lag가 데이터 길이의 20% 이상인 경우 잘못된 lag라는 에러가 발생하기 때문
        - 리스트는 최대 total_lags 길이를 가지며 최대한 동일한 간격인 lag들을 가집니다.
        """
        max_lags = 20

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
            - lag를 1에서 최대 15까지 계산한 후 귀무가설이 기각된 lag의 비율을 반환합니다.
        """
        SIGNIFICANCE_LEVEL = 0.01

        data = np.column_stack([self.xt, self.yt])
        lags = self._gen_lags_list(data.shape[0])

        with LogSuppressor():
            # verbose가 deprecated임에도, False로 설정하지 않으면 내부적으로 verbose=True가 됌
            # 이후 statsmodels 버전 업데이트 시 verbose 매개변수 제거하고 로그 출력 억제하는 법 알아봐야 함
            result = grangercausalitytests(
                data, maxlag=lags, addconst=True, verbose=False
            )

        p_values = []
        # 각 lag에 대한 검정 결과를 순회하며 p-value를 수집합니다.
        for lag, rst in result.items():
            for test in rst[0].values():
                p_values.append(test[1])
        dismissed_p_values = [v for v in p_values if v < SIGNIFICANCE_LEVEL]

        ratio = len(dismissed_p_values) / len(p_values)
        adj = 0.5  # 보다 엄격하게, 50% ~ 100% -> 0% ~ 100%
        return max(ratio - adj, 0) / (1 - adj)

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
        relationships = {}
        for pair in self.perm_pairs:
            value = PairwiseAnalyzer(
                xt=self.dataset[pair[0]].values,
                yt=self.dataset[pair[1]].values,
            ).grangercausality()
            if value:
                relationships[pair] = value
        filtered_relationships = relationships.copy()
        removal_candidates = []
        # 양방향 관계에서 Granger 인과관계 값이 낮은 쌍을 식별합니다.
        for (a, b), value in relationships.items():
            if (b, a) in relationships and (a, b) not in removal_candidates:
                if relationships[(a, b)] > relationships[(b, a)]:
                    removal_candidates.append((b, a))
                else:
                    removal_candidates.append((a, b))
        # 식별된 쌍 제거
        for pair in removal_candidates:
            if pair in filtered_relationships:
                del filtered_relationships[pair]
        return filtered_relationships

    def cointegration(self):
        result = {}
        for pair in self.comb_pairs:
            value = PairwiseAnalyzer(
                xt=self.dataset[pair[0]].values, yt=self.dataset[pair[1]].values
            ).cointegration()
            if value:
                result[pair] = value
        return result
