from functools import partial
from datetime import datetime, timedelta

import httpx
import psycopg
from fastapi import Body, Depends, HTTPException

from backend import db
from backend.system import EFS_VOLUME_PATH, log, MEMBERSHIP
from backend.math import utcstr2datetime, calc_next_billing_date
from backend.http import (
    APIRouter,
    PayPalAPI,
    PayPalWebhookAuth,
    TosspaymentsBilling,
    pooling,
)

router = APIRouter("webhook")


@router.public.post(
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
        if subscription["status"] != "ACTIVE":
            log.info(
                "[paypal webhook: PAYMENT.SALE.COMPLETED]"
                f"구독 상태가 'ACTIVE'가 아닙니다. 이벤트를 무시합니다. 구독 상태: {subscription['status']}"
                f"\nSummary: {event['summary']}, 구독 ID:{event['resource']['billing_agreement_id']}"
            )
            return {"message": "Apply success"}

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
        await pooling(  # 유저 생성 완료 전 요청 수신 시를 대비한 풀링
            db_insert_func, exceptions=psycopg.errors.NotNullViolation, timeout=30
        )
        await db.exec(
            """
            UPDATE users  
            SET next_billing_date={next_billing_date}, 
                current_billing_date={current_billing_date}, 
                origin_billing_date=base_billing_date, 
                billing_status='active'
            WHERE paypal_subscription_id={subscription_id};""",
            params={
                "next_billing_date": next_billing,
                "current_billing_date": transaction_time,
                "subscription_id": subscription_id,
            },
        )
        user = await db.select_row(
            table="users",
            fields=["email"],
            where={"paypal_subscription_id": subscription_id},
        )
        log.info(
            f"맴버십 비용 청구 완료({plan['name']})[Paypal]: "
            f"User(Email: {user['email']}, membership: {plan['name']})"
        )
    except psycopg.errors.NotNullViolation:
        subscription_id = event["resource"]["billing_agreement_id"]
        await PayPalAPI(f"/v1/billing/subscriptions/{subscription_id}/suspend").post(
            {"reason": "User that does not exist in Econox"}
        )
        log.warning(
            "[paypal webhook: PAYMENT.SALE.COMPLETED]"
            "구독에 해당하는 유저가 존재하지 않습니다. Paypal에서 해당 구독을 중지하였습니다."
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


@router.public.get("/billing")
async def billing():
    """
    - 스케쥴링된 람다가 주기적으로 호출해야 하는 웹훅 API
    - Tosspayments 유저의 반복 결제를 수행한다.
    - 대금이 지불되지 않았거나 비활성화된 계정의 맴버십 유효기간이 지난 경우 계정을 비활성화한다.
    """

    idempotent_mark = EFS_VOLUME_PATH / "processing_on_billing"
    if idempotent_mark.exists():
        return {"message": "There are processors that already do this"}
    idempotent_mark.write_text("")

    target_users = await db.exec(
        """
        SELECT id, email, currency, membership, base_billing_date, next_billing_date, tosspayments_billing_key, billing_status
        FROM users WHERE next_billing_date < now();
        """
    )
    now = datetime.now()
    db_transaction = db.Transaction()
    for user in target_users:
        (
            user_id,
            email,
            currency,
            membership,
            base_billing_date,
            next_billing_date,
            tosspayments_billing_key,
            billing_status,
        ) = user
        if next_billing_date < now - timedelta(days=3) or (
            next_billing_date < now and billing_status == "deactive"
        ):  # 결제가 누락된 경우 3일 버퍼를 주고, 사용자가 비활성화를 선택한 경우 즉시 계정을 비활성화
            db_transaction.append(
                "UPDATE users SET billing_status='require' WHERE id={user_id}",
                user_id=user_id,
            )
            log.info(
                f"GET /webhook/billing: 대금 미지급으로 인한 계정 비활성화 - "
                f"User(Email: {email}, membership: {membership}, next_billing_date: {next_billing_date})"
            )
        elif currency == "KRW" and tosspayments_billing_key:  # Tosspayments 결제
            try:
                payment = await TosspaymentsBilling(user_id=str(user_id)).billing(
                    tosspayments_billing_key,
                    order_name=f"Econox {membership.capitalize()} Membership",
                    amount=MEMBERSHIP[membership][currency],
                    email=email,
                )
            except httpx.HTTPStatusError as e:
                log.info(
                    f"[{e}] GET /webhook/billing: Tosspayments 맴버십 비용 청구 실패 - "
                    f"User(Email: {email}, membership: {membership}, next_billing_date: {next_billing_date})"
                )
                continue
            db_transaction.append(
                template=db.Template(table="tosspayments_billings").insert_query(
                    user_id=user_id,
                    order_id=payment["orderId"],
                    transaction_time=datetime.fromisoformat(payment["approvedAt"]),
                    payment_key=payment["paymentKey"],
                    order_name=payment["orderName"],
                    total_amount=payment["totalAmount"],
                    supply_price=payment["suppliedAmount"],
                    vat=payment["vat"],
                    card_issuer=payment["card"]["issuerCode"],
                    card_acquirer=payment["card"]["acquirerCode"],
                    card_number_masked=payment["card"]["number"],
                    card_approve_number=payment["card"]["approveNo"],
                    card_type=payment["card"]["cardType"],
                    card_owner_type=payment["card"]["ownerType"],
                    receipt_url=payment["receipt"]["url"],
                )
            )
            db_transaction.append(
                """ 
                UPDATE users 
                SET next_billing_date={next_billing_date}, 
                    origin_billing_date=base_billing_date,
                    current_billing_date={current_billing_date},
                    billing_status='active'
                WHERE id={user_id};""",
                next_billing_date=calc_next_billing_date(base_billing_date, now),
                current_billing_date=now,
                user_id=user_id,
            )
            log.info(
                f"맴버십 비용 청구 완료({membership})[Tosspayments]: "
                f"User(Email: {email}, membership: {membership})"
            )
    await db_transaction.exec()
    idempotent_mark.unlink(missing_ok=True)
    return {"message": "Process complete"}
