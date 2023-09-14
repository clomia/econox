import math
from datetime import datetime, timedelta

membership = {
    "basic": {
        "KRW": 11900,
        "USD": 9.99,
        "paypal_plan": "P-32P35738U4826650TMT72TNA",
    },
    "professional": {
        "KRW": 15900,
        "USD": 12.99,
        "paypal_plan": "P-8U118819R1222424SMT72UDI",
    },
}


def calculate_membership_expiry(start: datetime, current: datetime):
    """
    - start: 맴버십 시작일
    - current: 최근 청구 날짜
    - 맴버십 만료일을 계산합니다
    - 다음달 동일 일시를 구하되 마지막 일보다 크면 마지막 일로 대체
    - PayPal에서 사용하는 알고리즘과 동일합니다.
    """
    year, month, day = current.year, current.month, start.day

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

    return datetime(year, next_month, day)


def adjust_billing_date_for_membership_change(
    start_billing: datetime,
    current_billing: datetime,
    current_membership: str,
    new_membership: str,
    change_day: datetime,
    currency: str,
):
    """
    - start_billing: 청구 시작 날짜
    - last_billing: 마지막 청구 날짜
    - current_membership: 현재 맴버십
    - new_membership: 변경할 맴버십
    - change_day: 맴버십 변경 날짜
    - return: 다음 청구 날짜
    """

    next_billing = calculate_membership_expiry(start_billing, current_billing)

    membership_days = (next_billing - current_billing).days
    current_daily_amount = membership[current_membership][currency] / membership_days
    new_daily_amount = membership[new_membership][currency] / membership_days

    remaining_days = (next_billing - change_day).days
    remaining_amount = remaining_days * current_daily_amount

    new_remaining_days = math.floor(remaining_amount / new_daily_amount)
    return change_day + timedelta(days=new_remaining_days)


test_cases = [
    {
        "start_billing": datetime(2023, 4, 13),
        "current_billing": datetime(2023, 4, 13),
        "current_membership": "basic",
        "new_membership": "professional",
        "change_day": datetime(2023, 5, 12),
        "currency": "USD",
    },
    {
        "start_billing": datetime(2023, 4, 13),
        "current_billing": datetime(2023, 8, 13),
        "current_membership": "professional",
        "new_membership": "basic",
        "change_day": datetime(2023, 8, 24),
        "currency": "USD",
    },
    {
        "start_billing": datetime(2023, 4, 13),
        "current_billing": datetime(2023, 4, 13),
        "current_membership": "basic",
        "new_membership": "professional",
        "change_day": datetime(2023, 4, 20),
        "currency": "USD",
    },
    {
        "start_billing": datetime(2023, 4, 13),
        "current_billing": datetime(2023, 4, 13),
        "current_membership": "basic",
        "new_membership": "professional",
        "change_day": datetime(2023, 4, 20),
        "currency": "USD",
    },
]

results = []
for test in test_cases:
    print(f"change day: {test['change_day']}")
    print(f"start_billing: {test['start_billing']}")
    result = adjust_billing_date_for_membership_change(
        test["start_billing"],
        test["current_billing"],
        test["current_membership"],
        test["new_membership"],
        test["change_day"],
        test["currency"],
    )
    print(str(result) + "\n\n\n")
    results.append(result)


def adjust_billing_date_for_membership_change_v2(  # from gpt
    start_billing: datetime,
    current_billing: datetime,
    current_membership: str,
    new_membership: str,
    change_day: datetime,
    currency: str,
):
    """
    - start_billing: 청구 시작 날짜
    - current_billing: 마지막 청구 날짜
    - current_membership: 현재 맴버십
    - new_membership: 변경할 맴버십
    - change_day: 맴버십 변경 날짜
    - return: 다음 청구 날짜
    """

    next_billing = calculate_membership_expiry(start_billing, current_billing)
    membership_days = (next_billing - current_billing).days

    current_daily_amount = membership[current_membership][currency] / membership_days
    new_daily_amount = membership[new_membership][currency] / membership_days

    remaining_days = (next_billing - change_day).days
    remaining_amount = remaining_days * current_daily_amount
    adjusted_days = math.floor(remaining_amount / new_daily_amount)

    if current_daily_amount < new_daily_amount:  # upgrade
        return change_day + timedelta(days=adjusted_days)
    else:  # downgrade
        return next_billing + timedelta(days=adjusted_days - remaining_days)
