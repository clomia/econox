""" 모듈로 분류하기 어려운 앤드포인트들 """
from functools import partial
from datetime import timezone, timedelta

import psycopg
from fastapi import Body, Depends, HTTPException

from backend import db
from backend.math import paypaltime2datetime
from backend.http import APIRouter, PayPalAPI, PayPalWebhookAuth, pooling
from backend.system import SECRETS, MEMBERSHIP, log

router = [
    setting := APIRouter("setting"),
    webhook := APIRouter("webhook"),
]

KST = timezone(timedelta(hours=9))  # 타임존이 포함된 isoformat 문자열 생성에 필요


@setting.public.get("/paypal-plans")
async def paypal_info():
    return {
        "client_id": SECRETS["PAYPAL_CLIENT_ID"],
        "plan_id": {
            "basic": MEMBERSHIP["basic"]["paypal_plan"],
            "professional": MEMBERSHIP["professional"]["paypal_plan"],
        },
    }


@webhook.public.post(
    "/paypal/payment-sale-complete",
    dependencies=[Depends(PayPalWebhookAuth("PAYMENT.SALE.COMPLETED"))],
)  # PayPal 결제 완료 웹훅 API
async def paypal_payment_webhook(event: dict = Body(...)):
    if (event_type := event.get("event_type")) != "PAYMENT.SALE.COMPLETED":
        raise HTTPException(status_code=400, detail=f"Invalid event type: {event_type}")
    try:
        subscription_id = event["resource"]["billing_agreement_id"]
        subscription = await PayPalAPI(
            f"/v1/billing/subscriptions/{subscription_id}"
        ).get()
        plan = await PayPalAPI(f"/v1/billing/plans/{subscription['plan_id']}").get()
        insert_func = partial(
            db.exec,
            """
            INSERT INTO paypal_billings (user_id, transaction_id, transaction_time, 
                order_name, total_amount, fee_amount)
            VALUES (
                (SELECT id FROM users WHERE paypal_subscription_id={subscription_id} LIMIT 1),
                {transaction_id}, {transaction_time}, {order_name}, {total_amount}, {fee_amount}
            )
            """,
            silent=True,
            subscription_id=subscription_id,
            transaction_id=event["resource"]["id"],
            transaction_time=paypaltime2datetime(event["resource"]["create_time"]),
            order_name=plan["name"],
            total_amount=float(event["resource"]["amount"]["total"]),
            fee_amount=float(event["resource"]["transaction_fee"]["value"]),
        )
        await pooling(  # 회원가입 결제시 유저 생성 완료까지 풀링해야 될 수 있음
            insert_func, exceptions=psycopg.errors.NotNullViolation, timeout=30
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
