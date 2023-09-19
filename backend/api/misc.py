""" 모듈로 분류하기 어려운 앤드포인트들 """
from functools import partial
from datetime import datetime, timezone, timedelta

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
    subscription_id = event["resource"]["billing_agreement_id"]

    now = datetime.now(KST)
    start = (now - timedelta(days=2)).isoformat()
    end = now.isoformat()
    resp = await PayPalAPI(  # 구독에 대한 이틀치 트렌젝션 리스트를 가져온다
        f"/v1/billing/subscriptions/{subscription_id}/transactions"
    ).get(params={"start_time": start, "end_time": end})

    if transactions := resp.get("transactions"):
        last_transaction: dict = sorted(
            transactions,
            key=lambda x: datetime.fromisoformat(x["time"].replace("Z", "+00:00")),
        )[-1]
    else:
        log.warning(
            "[paypal webhook: PAYMENT.SALE.COMPLETED]"
            "PayPal에서 구독에 대한 트렌젝션 데이터를 찾지 못했습니다."
            f"\nSummary: {event['summary']}, 구독 ID:{subscription_id}"
        )  # 4xx 응답 시 paypal이 좀 이따가 웹훅을 재호출해줌, 좀 있으면 데이터 있을 수 있으므로 이렇게 예외 처리
        raise HTTPException(status_code=404, detail="No data to apply")

    amount_info = last_transaction["amount_with_breakdown"]
    try:
        insert_func = partial(
            db.exec,
            """
            INSERT INTO paypal_billings (user_id, transaction_id, transaction_time, 
                total_amount, fee_amount, net_amount)
            VALUES (
                (SELECT id FROM users WHERE paypal_subscription_id={subscription_id} LIMIT 1),
                {transaction_id}, {transaction_time}, {total_amount}, {fee_amount}, {net_amount}
            )
            """,
            silent=True,
            subscription_id=subscription_id,
            transaction_id=last_transaction["id"],
            transaction_time=paypaltime2datetime(last_transaction["time"]),
            total_amount=amount_info["gross_amount"]["value"],
            fee_amount=amount_info["fee_amount"]["value"],
            net_amount=amount_info["net_amount"]["value"],
        )
        await pooling(  # 회원가입 결제시 유저 생성 완료까지 풀링해야 될 수 있음
            insert_func, exceptions=psycopg.errors.NotNullViolation, timeout=60
        )
    except psycopg.errors.NotNullViolation:
        log.warning(
            "[paypal webhook: PAYMENT.SALE.COMPLETED]"
            "구독에 해당하는 유저가 존재하지 않습니다."
            f"\nSummary: {event['summary']}, 구독 ID:{subscription_id}"
        )
    except psycopg.errors.UniqueViolation:
        log.warning(  # transaction_id 필드의 UNIQUE 제약에 걸린 경우임
            "[paypal webhook: PAYMENT.SALE.COMPLETED]"
            "멱등 처리: 중복된 트렌젝션을 수신하였기 때문에 무시합니다."
            f"\nSummary: {event['summary']}, 구독 ID:{subscription_id}"
        )

    return {"message": "Apply success"}
