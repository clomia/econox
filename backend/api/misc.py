""" 모듈로 분류하기 어려운 앤드포인트들 """
from datetime import datetime

import ipinfo
from fastapi import Request, HTTPException

from backend import db
from backend.system import SECRETS, MEMBERSHIP, log
from backend.math import (
    datetime2utcstr,
    calc_next_billing_date,
    calc_next_billing_date_adjust_membership_change,
)
from backend.http import APIRouter

router = [
    country := APIRouter("country"),
    paypal := APIRouter("paypal"),
]


@country.public.get()
async def get_request_country(request: Request):
    """
    - 요청이 이루어진 국가 정보를 응답합니다.
    - Response: 국가와 타임존 정보
    """
    header = {k.casefold(): v for k, v in request.headers.items()}
    # AWS ELB는 헤더의 x-forwarded-for에 원본 ip를 넣어준다.
    ip = header.get("x-forwarded-for", request.client.host)
    try:
        handler = ipinfo.getHandlerAsync(SECRETS["IPINFO_API_KEY"])
        client_info = await handler.getDetails(ip)
        return {
            "country": client_info.country,
            "timezone": client_info.timezone,
        }
    except AttributeError:  # if host is localhost
        # default = {"country": "KR", "timezone": "Asia/Seoul"}
        default = {"country": "US", "timezone": "America/Chicago"}
        log.warning(
            "GET /country"
            f"\n국가 정보 취득에 실패했습니다. 기본값을 응답합니다."
            f"\nIP: {request.client.host} , 응답된 기본값: {default}"
        )
        return default
    finally:
        await handler.deinit()


@paypal.public.get("/plans")
async def paypal_plan_info():
    """
    - Response: JS SDK로 PayPal 위젯을 띄우는데 필요한 정보들
    """
    return {
        "client_id": SECRETS["PAYPAL_CLIENT_ID"],
        "plan_id": {
            "basic": MEMBERSHIP["basic"]["paypal_plan"],
            "professional": MEMBERSHIP["professional"]["paypal_plan"],
        },
    }


@paypal.private.get("/membership-change-subscription-start-time")
async def calculation_of_next_billing_date_according_to_membership_change(
    new_membership: str, user=paypal.private.user
):
    """
    - PayPal 유저의 맴버십 변경 시 PATCH /api/user/membership 호출 이전에 이 API로 구독 시작일을 계산한 뒤
        브라우저에서 SDK를 통해 구독을 생성해야 함
    - Response: PayPal Create subscription API의 start_time 매개변수로 넣어줘야 하는 날짜 조정값
        - adjusted_next_billing:
            - PATCH /api/user/membership 호출 시 사용
            - PayPal SDK 생성 시 start_time 매개변수로 사용
    """
    if user["currency"] != "USD":
        raise HTTPException(status_code=409, detail="The user does not use PayPal.")
    if user["membership"] == new_membership or new_membership not in MEMBERSHIP:
        raise HTTPException(
            status_code=409,
            detail=f"The {new_membership} membership is either identical to the already set value or invalid",
        )
    if user["origin_billing_date"] == user["base_billing_date"]:  # 맴버십 변경
        adjusted_next_billing = calc_next_billing_date_adjust_membership_change(
            base_billing=user["base_billing_date"],
            current_billing=user["current_billing_date"],
            current_membership=user["membership"],
            new_membership=new_membership,
            change_day=datetime.now(),
            currency="USD",
        )
    else:  # 변경된 맴버십 롤백
        adjusted_next_billing = calc_next_billing_date(
            base=user["origin_billing_date"], current=user["current_billing_date"]
        )
    return {"adjusted_next_billing": datetime2utcstr(adjusted_next_billing)}
