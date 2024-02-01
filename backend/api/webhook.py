from datetime import datetime, timedelta

import httpx
import psycopg
from fastapi import Body, Depends, HTTPException

from backend import db
from backend.system import Idempotent, log, MEMBERSHIP
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
        plan = await PayPalAPI(f"/v1/billing/plans/{subscription['plan_id']}").get()
        user = await pooling(  # 유저 생성이 완료되기 전에 요청을 수신했을 때를 대비한 풀링
            db.SQL(
                "SELECT * FROM users WHERE paypal_subscription_id={sid} LIMIT 1",
                params={"sid": subscription_id},
                fetch="one",
            ).exec,
            inspecter=lambda db_user: db_user is not None,
            timeout=10,
        )  # 계속 시도했는데 해당하는 유저가 없는 경우 AssertionError
        await db.InsertSQL(
            "paypal_billings",
            user_id=user["id"],
            transaction_id=event["resource"]["id"],
            transaction_time=transaction_time,
            order_name=plan["name"],
            total_amount=float(event["resource"]["amount"]["total"]),
            fee_amount=float(event["resource"]["transaction_fee"]["value"]),
        ).exec()
        next_billing_time = subscription["billing_info"]["next_billing_time"]
        await db.SQL(
            """
            UPDATE users  
            SET next_billing_date={next_billing_date}, 
                current_billing_date={current_billing_date}, 
                origin_billing_date=base_billing_date, 
                billing_status='active'
            WHERE paypal_subscription_id={subscription_id}""",
            params={
                "next_billing_date": utcstr2datetime(next_billing_time),
                "current_billing_date": transaction_time,
                "subscription_id": subscription_id,
            },
        ).exec()
        log.info(
            "맴버십 비용 청구 완료 [Paypal]: "
            f"User(Email: {user['email']}, Membership: {user['membership']})"
        )
    except AssertionError:
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
@Idempotent(default={"message": "There are processors that already do this"})
async def billing():
    """
    - 스케쥴링된 람다가 주기적으로 호출해야 하는 웹훅 API
    - Tosspayments 유저의 반복 결제를 수행한다.
    - 대금이 지불되지 않았거나 비활성화된 계정의 맴버십 유효기간이 지난 경우 계정을 비활성화한다.
    """

    query = "SELECT * FROM users WHERE next_billing_date < now() AND NOT billing_status='require'"
    target_users = await db.SQL(query, fetch="all").exec()
    if not target_users:
        log.info(f"[GET /webhook/billing: No Action] 비용 처리가 필요한 유저가 없습니다.")
        return {"message": "Process complete (No Action)"}

    now = datetime.now()
    deactive = failure = complete = 0
    deactive_detail = {
        "non_payer": 0,
        "deactivater": 0,
        "benefit_end": 0,
    }
    sql_list = []

    for user in target_users:
        # 결제가 누락된 유저, 결제일 3일 이후까지 유예기간으로 보고 3일동안 계속 결제를 시도함
        is_non_payer = user["next_billing_date"] < now - timedelta(days=3)
        # 결제 비활성화를 선택한 유저는 즉시 상태 적용
        is_deactivater = user["billing_status"] == "deactive"
        # 최초 회원가입 혜택이 종료된 유저도 즉시 상태 적용
        is_benefit_end = not user["origin_billing_date"]

        # 계정 비활성화 대상자 처리
        if any([is_non_payer, is_deactivater, is_benefit_end]):
            sql_list.append(
                db.SQL(
                    "UPDATE users SET billing_status='require' WHERE id={id}",
                    params={"id": user["id"]},
                )
            )
            log.info(
                f"GET /webhook/billing: 대금 미지급으로 계정 비활성화 - "
                f"User(Email: {user['email']}, membership: {user['membership']}, next_billing_date: {user['next_billing_date']})"
            )
            deactive += 1
            if is_benefit_end:
                deactive_detail["benefit_end"] += 1
            elif is_deactivater:
                deactive_detail["deactivater"] += 1
            elif is_non_payer:
                deactive_detail["non_payer"] += 1
        # Tosspayments 결제 대상자 처리 (PayPal 결제 대상자 처리는 paypal_payment_webhook 에서 함)
        elif user["currency"] == "KRW" and user["tosspayments_billing_key"]:
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

    result = (
        f"비용 처리가 필요한 대상자는 {len(target_users)}명입니다. "
        f"{complete}명에게 청구를 완료하였으며 청구에 실패한 미납자는 {failure}명 입니다. "
        f"또한, 3일 이상 청구에 실패한 {deactive_detail['non_payer']}명과 "
        f"3일 무료 혜택이 종료된 {deactive_detail['benefit_end']}명, "
        f"그리고 결제 중지가 요청된 {deactive_detail['deactivater']}명까지 "
        f"총 {deactive}개의 계정을 비활성화 하였습니다."
    )
    log.info("[GET /webhook/billing: 맴버십 비용 처리 완료] " + result)
    return {"message": result, "target_users": target_users}
