""" 모듈로 분류하기 어려운 앤드포인트들 """
from functools import partial
from datetime import datetime

import ipinfo
import psycopg
from fastapi import Request, Body, Depends, HTTPException

from backend import db
from backend.math import (
    utcstr2datetime,
    datetime2utcstr,
    calc_next_billing_date,
    calc_next_billing_date_adjust_membership_change,
)
from backend.http import APIRouter, PayPalAPI, PayPalWebhookAuth, pooling
from backend.system import SECRETS, MEMBERSHIP, log

router = [
    country := APIRouter("country"),
    paypal := APIRouter("paypal"),
    webhook := APIRouter("webhook"),
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
        default = {"country": "KR", "timezone": "Asia/Seoul"}
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
    new_membership: str, user=paypal.private.auth
):
    """
    - PayPal 유저의 맴버십 변경 시 PATCH /api/user/membership 호출 이전에 이 API로 구독 시작일을 계산한 뒤
        브라우저에서 SDK를 통해 구독을 생성해야 함
    - Response: PayPal Create subscription API의 start_time 매개변수로 넣어줘야 하는 날짜 조정값
        - adjusted_next_billing:
            - PATCH /api/user/membership 호출 시 사용
            - PayPal SDK 생성 시 start_time 매개변수로 사용
    """
    db_user = await db.select_row(
        "users",
        fields=[
            "membership",
            "currency",
            "origin_billing_date",
            "base_billing_date",
            "current_billing_date",
        ],
        where={"id": user["id"]},
    )
    if db_user["currency"] != "USD":
        raise HTTPException(status_code=409, detail="The user does not use PayPal.")
    if db_user["membership"] == new_membership or new_membership not in MEMBERSHIP:
        raise HTTPException(
            status_code=409,
            detail=f"The {new_membership} membership is either identical to the already set value or invalid",
        )
    if db_user["origin_billing_date"] == db_user["base_billing_date"]:  # 맴버십 변경
        adjusted_next_billing = calc_next_billing_date_adjust_membership_change(
            base_billing=db_user["base_billing_date"],
            current_billing=db_user["current_billing_date"],
            current_membership=db_user["membership"],
            new_membership=new_membership,
            change_day=datetime.now(),
            currency="USD",
        )
    else:  # 변경된 맴버십 롤백
        adjusted_next_billing = calc_next_billing_date(
            base=db_user["origin_billing_date"], current=db_user["current_billing_date"]
        )
    return {"adjusted_next_billing": datetime2utcstr(adjusted_next_billing)}


@webhook.public.post(
    "/paypal/payment-sale-complete",
    dependencies=[Depends(PayPalWebhookAuth("PAYMENT.SALE.COMPLETED"))],
)  # PayPal 결제 완료 웹훅 API
async def paypal_payment_webhook(event: dict = Body(...)):
    """
    - PayPal에서 PAYMENT.SALE.COMPLETED 이벤트에 대해 호출하는 웹훅 엔드포인트
    - PayPal 결제 완료 상태를 서버에 적용합니다.
    """
    if (event_type := event.get("event_type")) != "PAYMENT.SALE.COMPLETED":
        raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")
    try:
        transaction_time = utcstr2datetime(event["resource"]["create_time"])
        subscription_id = event["resource"]["billing_agreement_id"]
        subscription = await PayPalAPI(
            f"/v1/billing/subscriptions/{subscription_id}"
        ).get()
        next_billing = utcstr2datetime(
            subscription["billing_info"]["next_billing_time"]
        )
        plan = await PayPalAPI(f"/v1/billing/plans/{subscription['plan_id']}").get()
        db_insert_func = partial(
            db.exec,
            """
            INSERT INTO paypal_billings (user_id, transaction_id, transaction_time, 
                order_name, total_amount, fee_amount)
            VALUES (
                (SELECT id FROM users WHERE paypal_subscription_id={subscription_id} LIMIT 1),
                {transaction_id}, {transaction_time}, {order_name}, {total_amount}, {fee_amount}
            )
            """,
            params={
                "subscription_id": subscription_id,
                "transaction_id": event["resource"]["id"],
                "transaction_time": transaction_time,
                "order_name": plan["name"],
                "total_amount": float(event["resource"]["amount"]["total"]),
                "fee_amount": float(event["resource"]["transaction_fee"]["value"]),
            },
            silent=True,
        )
        await pooling(  # 유저 생성 완료 전 요청 수신 시를 대비한 풀링 로직
            db_insert_func, exceptions=psycopg.errors.NotNullViolation, timeout=30
        )
        await db.exec(
            """
            UPDATE users  
            SET next_billing_date={next_billing_date}, origin_billing_date=base_billing_date
            WHERE paypal_subscription_id={subscription_id};
            """,
            params={
                "next_billing_date": next_billing,
                "subscription_id": subscription_id,
            },
        )
    except psycopg.errors.NotNullViolation:
        log.warning(
            "[paypal webhook: PAYMENT.SALE.COMPLETED]"
            "구독에 해당하는 유저가 존재하지 않습니다."
            f"\nSummary: {event['summary']}, 구독 ID:{event['resource']['billing_agreement_id']}"
        )
    except psycopg.errors.UniqueViolation:
        log.warning(  # transaction_id 필드의 UNIQUE 제약에 걸린 경우임
            "[paypal webhook: PAYMENT.SALE.COMPLETED]"
            "멱등 처리: 중복된 트렌젝션을 수신하였기 때문에 무시합니다."
            f"\nSummary: {event['summary']}, 구독 ID:{event['resource']['billing_agreement_id']}"
        )
    except KeyError:
        log.warning(
            "[paypal webhook: PAYMENT.SALE.COMPLETED]"
            "KeyError: 검사에 성공했지만 내용이 올바르지 않습니다."
            f"\nevent: {event}"
        )

    return {"message": "Apply success"}
