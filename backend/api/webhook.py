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
        insert_sql = db.SQL(
            """
            INSERT INTO paypal_billings (user_id, transaction_id, transaction_time, 
                order_name, total_amount, fee_amount)
            VALUES (
                (SELECT id FROM users WHERE paypal_subscription_id={subscription_id} LIMIT 1),
                {transaction_id}, {transaction_time}, {order_name}, {total_amount}, {fee_amount}
            )""",
            params={
                "subscription_id": subscription_id,
                "transaction_id": event["resource"]["id"],
                "transaction_time": transaction_time,
                "order_name": plan["name"],
                "total_amount": float(event["resource"]["amount"]["total"]),
                "fee_amount": float(event["resource"]["transaction_fee"]["value"]),
            },
        )
        await pooling(  # 유저 생성이 완료되기 전에 요청을 수신했을 때를 대비한 풀링
            insert_sql.exec, exceptions=psycopg.errors.NotNullViolation, timeout=30
        )
        await db.SQL(
            """
            UPDATE users  
            SET next_billing_date={next_billing_date}, 
                current_billing_date={current_billing_date}, 
                origin_billing_date=base_billing_date, 
                billing_status='active'
            WHERE paypal_subscription_id={subscription_id}""",
            params={
                "next_billing_date": next_billing,
                "current_billing_date": transaction_time,
                "subscription_id": subscription_id,
            },
        ).exec()
        db_user = await db.SQL(
            "SELECT * FROM users WHERE paypal_subscription_id={subscription_id}",
            params={"subscription_id": subscription_id},
        ).exec()
        log.info(
            "맴버십 비용 청구 완료 [Paypal]: "
            f"User(Email: {db_user['email']}, Membership: {db_user['membership']})"
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
    # 이 함수가 완료되기전 프로세서가 종료되면 멱등로직으로 인해 수행 불가 상태가 됨
    # ECS 배포의 경우 기존 테스크의 처리 완료를 대기하므로 위와같은 문제는 발생하지 않음

    idempotent_mark = EFS_VOLUME_PATH / "processing_on_billing"
    if idempotent_mark.exists():
        return {"message": "There are processors that already do this"}
    idempotent_mark.write_text("")

    query = "SELECT * FROM users WHERE next_billing_date < now()"
    target_users = await db.SQL(query).exec()
    now = datetime.now()

    deactive = failure = complete = 0

    sql_list = []
    for user in target_users:
        if user["next_billing_date"] < now - timedelta(days=3) or (
            user["next_billing_date"] < now and user["billing_status"] == "deactive"
        ):  # 결제가 누락된 경우 3일 버퍼를 주고, 사용자가 비활성화를 선택한 경우 즉시 계정을 비활성화
            sql_list.append(
                db.SQL(
                    "UPDATE users SET billing_status='require' WHERE id={id}",
                    params={"id": user["id"]},
                )
            )
            log.info(
                f"GET /webhook/billing: 대금 미지급으로 인한 계정 비활성화 - "
                f"User(Email: {user['email']}, membership: {user['membership']}, next_billing_date: {user['next_billing_date']})"
            )
            deactive += 1
        elif user["currency"] == "KRW" and user["tosspayments_billing_key"]:
            # Tosspayments 결제
            try:
                payment = await TosspaymentsBilling(user_id=user["id"]).billing(
                    user["tosspayments_billing_key"],
                    order_name=f"Econox {user['membership'].capitalize()} Membership",
                    amount=MEMBERSHIP[user["membership"]][user["currency"]],
                    email=user["email"],
                )
            except httpx.HTTPStatusError as e:
                log.info(
                    f"[{e}] GET /webhook/billing: Tosspayments 맴버십 비용 청구 실패 - "
                    f"User(Email: {user['email']}, membership: {user['membership']}, next_billing_date: {user['next_billing_date']})"
                )
                failure += 1
                continue
            sql_list.append(
                db.InsertSQL(
                    "tosspayments_billings",
                    user_id=user["id"],
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
            next_billing_date = calc_next_billing_date(user["base_billing_date"], now)
            sql_list.append(
                db.SQL(
                    """ 
                UPDATE users 
                SET next_billing_date={next_billing_date}, 
                    origin_billing_date=base_billing_date,
                    current_billing_date={current_billing_date},
                    billing_status='active'
                WHERE id={user_id}""",
                    params={
                        "next_billing_date": next_billing_date,
                        "current_billing_date": now,
                        "user_id": user["id"],
                    },
                )
            )
            log.info(
                f"맴버십 비용 청구 완료 [Tosspayments]: "
                f"User(Email: {user['email']}, Membership: {user['membership']})"
            )
            complete += 1
    if sql_list:
        await db.exec(*sql_list, parallel=True)  # 각 쿼리가 모두 독립적므로 병렬 처리

    target_user_emails = [user["email"] for user in target_users]
    log.info(
        f"[GET /webhook/billing: Tosspayments 맴버십 비용 처리 완료] "
        f"처리가 필요한 유저는 {len(target_user_emails)}명입니다. "
        f"{complete}명에게 청구를 완료하였으며 청구에 실패한 미납자는 {failure}명 입니다. "
        f"3일 이상 청구에 실패하였거나 결제 중지가 요청된 {deactive}개의 계정을 비활성화 하였습니다."
    )
    idempotent_mark.unlink()
    return {"message": "Process complete"}
