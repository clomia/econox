""" /api/user """
import asyncio
from typing import Literal, List
from datetime import datetime, timedelta
from functools import partial

import httpx
import boto3
import psycopg
from pydantic import BaseModel, constr
from fastapi import HTTPException, Body

from backend import db
from backend.system import SECRETS, MEMBERSHIP, run_async
from backend.http import (
    APIRouter,
    TosspaymentsAPI,
    TosspaymentsBilling,
    PayPalAPI,
    pooling,
    get_paypal_next_billing_date,
)
from backend.math import (
    utcstr_type,
    utcstr2datetime,
    datetime2utcstr,
    calc_next_billing_date,
    calc_next_billing_date_adjust_membership_change,
)


router = APIRouter("user")
cognito = boto3.client("cognito-idp")


def payment_method_exists(user: dict) -> bool:
    """
    - 결제수단 등록 여부
    - user: get_user 함수를 통해 가져온 DB 유저 데이터
    """
    return bool(
        (user["currency"] == "KRW" and user["tosspayments_billing_key"])
        or (user["currency"] == "USD" and user["paypal_subscription_id"])
    )


class TosspaymentsBillingInfo(BaseModel):
    card_number: constr(min_length=1)
    expiration_year: constr(min_length=1)
    expiration_month: constr(min_length=1)
    owner_id: constr(min_length=1)


class PaypalBillingInfo(BaseModel):
    order: constr(min_length=1)  # order id
    subscription: constr(min_length=1)  # subscription id


class SignupInfo(BaseModel):
    email: constr(min_length=1)
    phone: constr(min_length=1)
    membership: Literal["basic", "professional"]
    currency: Literal["KRW", "USD"]
    # 첫 회원가입이 아닌 경우 둘 중 하나는 있어야 함
    tosspayments: TosspaymentsBillingInfo | None = None
    paypal: PaypalBillingInfo | None = None


@router.public.post()
async def signup(item: SignupInfo):
    """
    - 유저 생성 (회원가입)
    - 결제 정보가 누락되거나 잘못된 경우 402 응답
    - POST /api/user/cognito를 통해 이메일에 대한 Cognito 유저가 생성되어있어야 함
    - Response: 첫 회원가입 혜택 여부
    """

    try:
        cognito_user = await run_async(
            cognito.admin_get_user,
            UserPoolId=SECRETS["COGNITO_USER_POOL_ID"],
            Username=item.email,
        )
        user_id: str = cognito_user["Username"]
    except cognito.exceptions.UserNotFoundException:
        raise HTTPException(status_code=409, detail="Cognito user not found")
    if cognito_user["UserStatus"] != "CONFIRMED":
        raise HTTPException(status_code=401, detail="Cognito user is not confirmed")

    billing_method = None
    now = datetime.now()
    next_billing: datetime = calc_next_billing_date(base=now, current=now)
    signup_history = await db.signup_history_exists(email=item.email, phone=item.phone)
    if signup_history:
        # 회원가입 내역이 있다면 결제정보 필요함
        if item.currency == "KRW" and item.tosspayments:  # 토스페이먼츠 빌링
            tosspayments = TosspaymentsBilling(user_id)
            try:
                billing_key = await tosspayments.get_billing_key(
                    item.tosspayments.card_number,
                    item.tosspayments.expiration_year,
                    item.tosspayments.expiration_month,
                    item.tosspayments.owner_id,
                )
                payment = await tosspayments.billing(
                    billing_key,
                    order_name=f"Econox {item.membership.capitalize()} Membership",
                    amount=MEMBERSHIP[item.membership][item.currency],
                    email=item.email,
                )
            except httpx.HTTPStatusError:
                raise HTTPException(
                    status_code=402,
                    detail=f"[Tosspayments] Your payment information is incorrect.",
                )
            insert_tosspayments_billing = db.InsertSQL(
                "tosspayments_billings",
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
            billing_method = payment["card"]["number"]
        elif item.currency == "USD" and item.paypal:  # 페이팔 빌링
            # -- 빌링 성공여부 확인 --
            # DB 데이터 입력은 웹훅 API가 수행합니다.(POST /api/webhook/paypal/payment-sale-complete)
            order_detail_api = f"/v2/checkout/orders/{item.paypal.order}"
            subscription_detail_api = (
                f"/v1/billing/subscriptions/{item.paypal.subscription}"
            )
            try:
                order, subscription = await pooling(
                    target=partial(
                        asyncio.gather,  # 주문과 구독 정보를 가져옵니다.
                        PayPalAPI(order_detail_api).get(),
                        PayPalAPI(subscription_detail_api).get(),
                    ),
                    inspecter=(  # 주문 정보와 구독 정보가 완료상태인지 확인합니다.
                        lambda results: results[0]["status"] == "APPROVED"
                        and results[1]["status"] == "ACTIVE"
                    ),
                )  # timeout이 초과되어도 조건이 만족되지 않으면 AssertionError
                next_billing = utcstr2datetime(
                    subscription["billing_info"]["next_billing_time"]
                )
                billing_method = "Paypal"
            except (httpx.HTTPStatusError, AssertionError):
                raise HTTPException(
                    status_code=402,
                    detail=f"[PayPal] Your subscription or order status in paypal server is incorrect",
                )
        else:
            raise HTTPException(
                status_code=402,
                detail="Correct billing information is required",
            )

    tosspayments_billing_key = billing_key if item.tosspayments else None
    paypal_subscription_id = item.paypal.subscription if item.paypal else None
    insert_user = db.InsertSQL(  # 외래키 제약조건으로 인해 가장 먼저 실행되어야 함
        "users",
        id=user_id,
        email=item.email,
        name=item.email.split("@")[0][:10],
        phone=item.phone,
        membership=item.membership,
        currency=item.currency,
        origin_billing_date=now if signup_history else None,
        base_billing_date=now if signup_history else None,
        current_billing_date=now if signup_history else None,
        next_billing_date=next_billing,
        tosspayments_billing_key=tosspayments_billing_key,
        paypal_subscription_id=paypal_subscription_id,
        billing_method=billing_method,
    )
    insert_signup_history = db.InsertSQL(
        "signup_histories",
        user_id=user_id,
        email=item.email,
        phone=item.phone,
    )
    try:
        if item.currency == "KRW" and item.tosspayments:
            await db.exec(
                insert_user,
                insert_signup_history,
                insert_tosspayments_billing,
            )
        else:
            await db.exec(insert_user, insert_signup_history)
    except psycopg.errors.UniqueViolation:  # email colume is unique
        raise HTTPException(status_code=409, detail="Email is already in used")
    return {"first_signup_benefit": not signup_history}  # 첫 회원가입 혜택 여부


class BillingTransaction(BaseModel):
    time: utcstr_type
    name: constr(min_length=1)
    amount: float
    method: constr(min_length=1)  # 사용된 결제수단


class UserBillingDetail(BaseModel):
    currency: Literal["USD", "KRW"]
    registered: bool  # 결제수단 등록 여부
    status: Literal["active", "require", "deactive"]
    method: constr(min_length=1) | None  # 현재 등록되어있는 결제수단
    transactions: List[BillingTransaction]


class UserDetail(BaseModel):
    id: constr(min_length=1)
    name: constr(min_length=1)
    email: constr(min_length=1)
    membership: Literal["basic", "professional"]
    signup_date: utcstr_type
    next_billing_date: utcstr_type
    billing: UserBillingDetail


@router.private.get(response_model=UserDetail)
async def get_user_detail(user=router.private.user):
    """
    - 유저 상세 정보를 가져옵니다.
    - Response: UserDetail 스키마를 참조
    """
    detail = {
        "id": user["id"],
        "name": user["name"],
        "email": user["email"],
        "membership": user["membership"],
        "signup_date": datetime2utcstr(user["created"]),
        "next_billing_date": datetime2utcstr(user["next_billing_date"]),
        "billing": {
            "currency": user["currency"],
            "registered": payment_method_exists(user),
            "status": user["billing_status"],
            "method": user["billing_method"],
            "transactions": [],
        },
    }
    if user["currency"] == "KRW":
        query = "SELECT * FROM tosspayments_billings WHERE user_id={user_id} ORDER BY created DESC LIMIT 15"
        select_transactions = db.SQL(query, params={"user_id": user["id"]}, fetch="all")
        for transaction in await select_transactions.exec():
            detail["billing"]["transactions"].append(
                {
                    "time": datetime2utcstr(transaction["transaction_time"]),
                    "name": transaction["order_name"],
                    "amount": transaction["total_amount"],
                    "method": transaction["card_number_masked"],
                }
            )
    elif user["currency"] == "USD":
        query = "SELECT * FROM paypal_billings WHERE user_id={user_id} ORDER BY created DESC LIMIT 15"
        select_transactions = db.SQL(query, params={"user_id": user["id"]}, fetch="all")
        for transaction in await select_transactions.exec():
            detail["billing"]["transactions"].append(
                {
                    "time": datetime2utcstr(transaction["transaction_time"]),
                    "name": transaction["order_name"],
                    "amount": transaction["total_amount"],
                    "method": "PayPal",
                }
            )
    return detail


@router.private.delete()
async def user_delete(user=router.private.user):
    """
    - 회원 탈퇴
    - DB와 Cognito에서 유저 삭제
    - PayPal 사용자인 경우 구독 해지
        - Tosspayments 사용자는 DB 유저만 지워지면 결제 중지됨
    """
    if user["paypal_subscription_id"]:
        await PayPalAPI(
            f"/v1/billing/subscriptions/{user['paypal_subscription_id']}/cancel"
        ).post({"reason": "Delete account"})
    delete_user = db.SQL(
        "DELETE FROM users WHERE id={user_id}", params={"user_id": user["id"]}
    )
    update_signup_history_marking_as_user_deleted = db.SQL(
        "UPDATE signup_histories SET user_deleted=CURRENT_TIMESTAMP WHERE user_id={user_id}",
        params={"user_id": user["id"]},
    )
    await db.exec(delete_user, update_signup_history_marking_as_user_deleted)
    await run_async(cognito.delete_user, AccessToken=user["cognito_access_token"])
    return {"message": "Delete successfully"}


@router.public.post("/cognito")
async def create_cognito_user(
    email: str = Body(..., min_length=1),
    password: str = Body(..., min_length=6),
):
    """
    - AWS Cognito에 유저 생성 & 이메일로 인증코드 전송
    - POST /api/auth/email/confirm API로 해당 인증코드를 인증해야 함
    - Response: Cognito에서 생성된 유저 ID
    """
    if await db.get_user(email=email):
        raise HTTPException(status_code=409, detail="Email is already in used")
    create_cognito_user_func = partial(
        run_async,
        cognito.sign_up,
        ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
        Username=email,
        Password=password,
        UserAttributes=[{"Name": "email", "Value": email}],
    )
    try:  # cognito 유저 생성 실패에 대한 에러 응답 반환
        try:  # cognito 유저 생성, 만약 이미 있다면 삭제 후 재시도
            result = await create_cognito_user_func()
        except cognito.exceptions.UsernameExistsException:
            await run_async(
                cognito.admin_delete_user,
                UserPoolId=SECRETS["COGNITO_USER_POOL_ID"],
                Username=email,
            )
            result = await create_cognito_user_func()
    except (
        cognito.exceptions.InvalidParameterException,
        cognito.exceptions.CodeDeliveryFailureException,
    ):
        raise HTTPException(status_code=400, detail="Email is not valid")
    return {"cognito_id": result["UserSub"]}


@router.private.patch("/name")
async def change_user_name(
    new_name: str = Body(..., min_length=1, max_length=10, embed=True),
    user=router.private.user,
):
    """유저 이름 변경"""
    await db.SQL(
        "UPDATE users SET name={new_name} WHERE id={id}",
        params={"id": user["id"], "new_name": new_name},
    ).exec()
    return {"message": "Changed successfully"}


@router.public.patch("/password")
async def change_password(
    new_password: str = Body(..., min_length=6),
    confirm_code: str = Body(..., min_length=1),
    email: str = Body(..., min_length=1),
):
    """
    - 비밀번호를 변경합니다. (POST /api/auth/send-password-reset-code API를 통해 받은 인증코드가 필요합니다.)
    - send-password-reset-code API로 비밀번호를 재설정 코드를 전송한 뒤에 호출해야 합니다.
    - new_password: 변경 후 비밀번호
    - confirm_code: send-password-reset-code API를 통해 유저에게 발송된 인증코드
    - email: send-password-reset-code API에 사용한 이메일과 동일한 이메일
    """
    if not await db.get_user(email=email):
        raise HTTPException(status_code=404, detail="User does not exist")
    try:
        await run_async(
            cognito.confirm_forgot_password,
            ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
            Username=email,
            ConfirmationCode=confirm_code,
            Password=new_password,
        )
    except cognito.exceptions.LimitExceededException:
        raise HTTPException(status_code=429, detail="Too many requests")
    except cognito.exceptions.CodeMismatchException:
        raise HTTPException(status_code=409, detail="Invalid code")
    else:
        return {"message": "Password change successful"}


class MembershipChangeRequest(BaseModel):
    new_membership: constr(min_length=1)
    paypal_subscription_id: constr(min_length=1) | None = None


@router.private.patch("/membership")
async def change_membership(item: MembershipChangeRequest, user=router.private.user):
    """
    - 맴버십을 변경합니다.
    - new_membership: 변경 후 맴버십
    - paypal_subscription_id[Optional]: USD 통화를 사용하는 PayPal 유저인 경우 새로운 PayPal 구독 ID를 발급받아 입력
        - 구독 생성 시 GET /api/paypal/membership-change-subscription-start-time 를 사용하세요
    - Response: 조정된 다음 청구일시
    """
    if (  # new_membership값이 올바른지 확인
        user["membership"] == item.new_membership
        or item.new_membership not in MEMBERSHIP
    ):
        raise HTTPException(
            status_code=409,
            detail=f"The {item.new_membership} membership is either identical to the already set value or invalid",
        )

    update_query_trial = """
        UPDATE users SET membership={new_membership} WHERE id={user_id}
    """
    update_query_tosspayments = """
        UPDATE users 
        SET membership={new_membership}, 
            base_billing_date={base_billing_date},
            next_billing_date={next_billing}
        WHERE id={user_id}"""
    update_query_paypal = """
        UPDATE users 
        SET membership={new_membership}, 
            base_billing_date={base_billing_date},
            next_billing_date={next_billing},
            paypal_subscription_id={subscription_id}
        WHERE id={user_id}"""  # paypal_subscription_id 업데이트 필요

    if user["current_billing_date"] is None:  # 결제가 필요 없는 계정이므로 맴버십만 바꾸면 됌
        await db.SQL(
            update_query_trial,
            params={"new_membership": item.new_membership, "user_id": user["id"]},
        ).exec()
        adjusted_next_billing = user["next_billing_date"]
    elif user["origin_billing_date"] == user["base_billing_date"]:
        # 이전에 결제된 맴버십을 다른것으로 변경하는 경우
        if user["currency"] == "USD" and item.paypal_subscription_id:
            adjusted_next_billing = await get_paypal_next_billing_date(
                item.paypal_subscription_id  # 다음 청구 날짜는 이미 새로운 구독에 반영되어있음
            )
            cancel_reason = "A new subscription has been created to apply the difference due to the change in the plan."
            await PayPalAPI(  # 기존 구독 비활성화
                f"/v1/billing/subscriptions/{user['paypal_subscription_id']}/cancel"
            ).post({"reason": cancel_reason})
            await db.SQL(
                update_query_paypal,
                params={
                    "new_membership": item.new_membership,
                    "base_billing_date": adjusted_next_billing,
                    "next_billing": adjusted_next_billing,
                    "user_id": user["id"],
                    "subscription_id": item.paypal_subscription_id,
                },
            ).exec()
        elif user["currency"] == "KRW":
            # Tosspayments -> 다음 청구 날짜 직접 계산
            adjusted_next_billing = calc_next_billing_date_adjust_membership_change(
                base_billing=user["base_billing_date"],
                current_billing=user["current_billing_date"],
                current_membership=user["membership"],
                new_membership=item.new_membership,
                change_day=datetime.now(),
                currency=user["currency"],
            )
            await db.SQL(
                update_query_tosspayments,
                params={
                    "new_membership": item.new_membership,
                    "base_billing_date": adjusted_next_billing,
                    "next_billing": adjusted_next_billing,
                    "user_id": user["id"],
                },
            ).exec()
    else:  # 결제가 이루어지기 전에, 기존 맴버십으로 롤백하는 경우
        if user["currency"] == "USD" and item.paypal_subscription_id:
            adjusted_next_billing = await get_paypal_next_billing_date(
                item.paypal_subscription_id  # 다음 청구 날짜는 이미 새로운 구독에 반영되어있음
            )
            cancel_reason = "A new subscription has been created to apply the difference due to the change in the plan."
            await PayPalAPI(  # 기존 구독 비활성화
                f"/v1/billing/subscriptions/{user['paypal_subscription_id']}/cancel"
            ).post({"reason": cancel_reason})
            await db.SQL(
                update_query_paypal,
                params={
                    "new_membership": item.new_membership,
                    "base_billing_date": user["origin_billing_date"],  # 롤백
                    "next_billing": adjusted_next_billing,
                    "user_id": user["id"],
                    "subscription_id": item.paypal_subscription_id,
                },
            ).exec()
        elif user["currency"] == "KRW":
            adjusted_next_billing = calc_next_billing_date(
                base=user["origin_billing_date"],
                current=user["current_billing_date"],
            )
            await db.SQL(
                update_query_tosspayments,
                params={
                    "new_membership": item.new_membership,
                    "base_billing_date": user["origin_billing_date"],
                    "next_billing": adjusted_next_billing,
                    "user_id": user["id"],
                },
            ).exec()
    return {"adjusted_next_billing": datetime2utcstr(adjusted_next_billing)}


class PaymentMethodInfo(BaseModel):
    tosspayments: TosspaymentsBillingInfo | None = None
    paypal_subscription_id: str = None


@router.private.patch("/payment-method")
async def change_payment_method(item: PaymentMethodInfo, user=router.private.user):
    """결제수단을 변경합니다. PG사 변경은 불가능합니다."""
    if user["currency"] == "KRW" and item.tosspayments:
        tosspayments = TosspaymentsBilling(user_id=user["id"])
        try:
            billing_key = await tosspayments.get_billing_key(
                item.tosspayments.card_number,
                item.tosspayments.expiration_year,
                item.tosspayments.expiration_month,
                item.tosspayments.owner_id,
            )
            payment = await tosspayments.billing(
                billing_key, amount=100, order_name="Payment method confirmation"
            )  # 100원 결제
            await TosspaymentsAPI(  # 100원 환불
                f"/v1/payments/{payment['paymentKey']}/cancel"
            ).post({"cancelReason": "Confirmed"})
        except httpx.HTTPStatusError:
            raise HTTPException(
                status_code=402,
                detail=f"[Tosspayments] Your payment information is incorrect.",
            )
        await db.SQL(
            """
            UPDATE users 
            SET tosspayments_billing_key={billing_key},
                billing_method={billing_method}
            WHERE id={user_id}""",
            params={
                "billing_key": billing_key,
                "user_id": user["id"],
                "billing_method": payment["card"]["number"],
            },
        ).exec()
    elif user["currency"] == "USD" and item.paypal_subscription_id:  # 페이팔 빌링
        try:
            next_billing = await get_paypal_next_billing_date(
                item.paypal_subscription_id
            )
            await PayPalAPI(  # 기존 구독 취소
                f"/v1/billing/subscriptions/{user['paypal_subscription_id']}/cancel"
            ).post({"reason": "Change payment method"})
        except (AssertionError, httpx.HTTPStatusError):
            raise HTTPException(
                status_code=402,
                detail=f"[PayPal] Your subscription status in paypal server is incorrect",
            )
        await db.SQL(
            """
            UPDATE users SET paypal_subscription_id={subscription}, 
                next_billing_date={next_billing} 
            WHERE id={user_id}
            """,
            params={
                "subscription": item.paypal_subscription_id,
                "next_billing": next_billing,
                "user_id": user["id"],
            },
        ).exec()
    else:
        raise HTTPException(
            status_code=409,
            detail="Payment info doesn't match user's currency or user has no payment details",
        )
    return {"message": "Payment method updated"}


@router.private.post("/billing/deactivate")
async def deactivated_billing(user=router.private.user):
    """
    - 계정의 결제를 비활성화합니다. 이후 비용이 청구되지 않습니다.
    """
    if not payment_method_exists(user):
        raise HTTPException(
            status_code=402, detail="There is no registered payment method"
        )
    if not user["billing_status"] == "active":
        raise HTTPException(status_code=409, detail="Billing is already suspended")
    if user["paypal_subscription_id"]:
        await PayPalAPI(
            f"/v1/billing/subscriptions/{user['paypal_subscription_id']}/suspend"
        ).post({"reason": "Deactivate Billing"})
    await db.SQL(
        "UPDATE users SET billing_status='deactive' WHERE id={user_id}",
        params={"user_id": user["id"]},
    ).exec()
    return {"message": "User billing deactivated"}


class BillingRestore(BaseModel):
    tosspayments: TosspaymentsBillingInfo | None = None
    paypal: PaypalBillingInfo | None = None


@router.private.post("/billing/activate")
async def activate_billing(item: BillingRestore, user=router.private.user):
    """
    - 계정의 결제를 활성화합니다.
    - 먼저 토큰만 넣어서 호출해보고 402 응답을 수신하면 결제 정보를 넣어서 다시 호출하세요.
        - 결제 주기를 벗어나 비활성화된 계정에 대해서는 결제정보를 받아 다시 청구를 재개해야 하므로 402을 응답합니다.
        - 결제정보가 올바르지 않은 경우에도 402 에러가 응답됩니다.
    """
    is_benefit_end = not payment_method_exists(user)
    proper_payment_method_in_request = (  # 통화 종류에 맞는 결제 정보가 요청에 들어있는지 확인
        user["currency"] == "KRW" and item.tosspayments
    ) or (user["currency"] == "USD" and item.paypal)
    if is_benefit_end and not proper_payment_method_in_request:
        raise HTTPException(
            status_code=402,
            detail="Your first membership offer has ended, so we need your payment information",
        )
    if user["billing_status"] == "active":
        raise HTTPException(status_code=409, detail="You are already activated")

    sql_list = []
    now = datetime.now()
    if user["next_billing_date"] - timedelta(days=1) < now:  # 결제 주기를 벗어남 (계정 정지 상태)
        # 결제가 정확한 시간에 이루어지는게 아니라서 결제 예정일 하루 전을 기준으로 함, paypal 웹훅 딜레이 있어서 billing_status로 구분하면 안됌
        # 결제 예정일 당일에 처리하면 Paypal 결제 웹훅 처리와 중복되어 2번 결제, 구독될 위험성이 있기 때문
        if user["currency"] == "USD":  # Paypal
            if not item.paypal:
                raise HTTPException(
                    status_code=402,
                    detail="Paypal billing information is missing, you need a new paypal subscription",
                )
            next_billing_date = await get_paypal_next_billing_date(
                item.paypal.subscription  # 새로운 구독의 유효성 확인 & 다음 결제일 가져오기
            )
            if user["paypal_subscription_id"]:
                await PayPalAPI(  # 기존 paypal 구독 취소
                    f"/v1/billing/subscriptions/{user['paypal_subscription_id']}/cancel"
                ).post({"reason": "Reactivate Billing"})
            sql_list.append(
                db.SQL(
                    "UPDATE users SET paypal_subscription_id={subscription_id}, billing_method={method} WHERE id={user_id}",
                    params={
                        "subscription_id": item.paypal.subscription,
                        "method": "Paypal",
                        "user_id": user["id"],
                    },
                )
            )
        if user["currency"] == "KRW":  # Tosspayments
            if not item.tosspayments:
                raise HTTPException(
                    status_code=402,
                    detail="Tosspayments billing information is missing",
                )
            try:
                new_billing_key = await TosspaymentsBilling(
                    user_id=user["id"]
                ).get_billing_key(
                    card_number=item.tosspayments.card_number,
                    expiration_year=item.tosspayments.expiration_year,
                    expiration_month=item.tosspayments.expiration_month,
                    owner_id=item.tosspayments.owner_id,
                )
                payment = await TosspaymentsBilling(user_id=user["id"]).billing(
                    new_billing_key,  # 구독료 즉시 결제
                    order_name=f"Econox {user['membership'].capitalize()} Membership",
                    amount=MEMBERSHIP[user["membership"]][user["currency"]],
                    email=user["email"],
                )
            except httpx.HTTPStatusError:
                raise HTTPException(
                    status_code=402,
                    detail=f"[Tosspayments] Your payment information is incorrect.",
                )
            else:
                sql_list.append(
                    db.SQL(
                        "UPDATE users SET tosspayments_billing_key={new_key}, billing_method={method} WHERE id={id}",
                        params={
                            "new_key": new_billing_key,
                            "method": payment["card"]["number"],
                            "id": user["id"],
                        },
                    )
                )
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
            next_billing_date = calc_next_billing_date(base=now, current=now)
        sql_list.append(
            db.SQL(
                """
            UPDATE users 
            SET origin_billing_date={now}, base_billing_date={now}, 
                current_billing_date={now}, next_billing_date={next_billing_date}
            WHERE id={user_id};
            """,
                params={
                    "now": now,
                    "next_billing_date": next_billing_date,
                    "user_id": user["id"],
                },
            )
        )
    else:  # 아직 결제 주기 안에 있음 (계정 정지 예정인 상태)
        if user["currency"] == "USD" and user["paypal_subscription_id"]:
            try:
                await PayPalAPI(  # paypal 구독 재활성화
                    f"/v1/billing/subscriptions/{user['paypal_subscription_id']}/activate"
                ).post()
            except httpx.HTTPStatusError:
                raise HTTPException(
                    status_code=402,
                    detail=f"[PayPal] Your paypal status is incorrect. can't activate subscription",
                )
    sql_list.append(
        db.SQL(
            "UPDATE users SET billing_status='active' WHERE id={id}",
            params={"id": user["id"]},
        )
    )
    await db.exec(*sql_list)
    return {"message": "User billing activated"}
