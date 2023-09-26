""" /api/user """
import asyncio
from typing import Literal, List
from datetime import datetime
from functools import partial

import httpx
import boto3
import psycopg
from pydantic import BaseModel, constr
from fastapi import HTTPException, Body

from backend import db
from backend.system import SECRETS, run_async, MEMBERSHIP
from backend.http import (
    APIRouter,
    TosspaymentsAPI,
    TosspaymentsBilling,
    PayPalAPI,
    pooling,
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

    now = datetime.now()
    next_billing: datetime = calc_next_billing_date(base=now, current=now)

    signup_transaction = db.Transaction()
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

            signup_transaction.append(
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
                    timeout=30,  # 조건이 만족될때까지 최대 30초 재시도합니다.
                )  # timeout이 초과되어도 조건이 만족되지 않으면 AssertionError
                next_billing = utcstr2datetime(
                    subscription["billing_info"]["next_billing_time"]
                )
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
    signup_transaction.prepend(  # 외래키 제약조건으로 인해 가장 먼저 실행되어야 함
        template=db.Template(table="users").insert_query(
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
        )
    )
    signup_transaction.append(
        template=db.Template(table="signup_histories").insert_query(
            user_id=user_id,
            email=item.email,
            phone=item.phone,
        )
    )
    try:
        await signup_transaction.exec()
    except psycopg.errors.UniqueViolation:  # email colume is unique
        raise HTTPException(status_code=409, detail="Email is already in used")
    return {"first_signup_benefit": not signup_history}  # 첫 회원가입 혜택 여부


class BillingTransaction(BaseModel):
    time: utcstr_type
    name: constr(min_length=1)
    amount: float
    method: constr(min_length=1)


class UserBillingDetail(BaseModel):
    currency: Literal["USD", "KRW"]
    registered: bool
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
async def get_user_detail(user=router.private.auth):
    """유저 상세 정보를 가져옵니다."""
    (
        name,
        membership,
        currency,
        next_billing,
        tosspayments_billing_key,
        paypal_subscription_id,
        created,
    ) = await db.exec(
        template=db.Template(table="users").select_query(
            "name",
            "membership",
            "currency",
            "next_billing_date",
            "tosspayments_billing_key",
            "paypal_subscription_id",
            "created",
            where={"id": user["id"]},
        ),
        embed=True,
    )
    registered = bool(
        (currency == "KRW" and tosspayments_billing_key)
        or (currency == "USD" and paypal_subscription_id)
    )
    detail = {
        "id": user["id"],
        "name": name,
        "email": user["email"],
        "membership": membership,
        "signup_date": datetime2utcstr(created),
        "next_billing_date": datetime2utcstr(next_billing),
        "billing": {"currency": currency, "registered": registered, "transactions": []},
    }
    transaction_fields = ["time", "name", "amount", "method"]

    cond_kwargs = {"where": {"user_id": user["id"]}, "limit": 15}
    if currency == "KRW":
        transactions: list = await db.exec(
            template=db.Template(table="tosspayments_billings").select_query(
                "transaction_time",
                "order_name",
                "total_amount",
                "card_number_masked",
                **cond_kwargs,
            )
        )
        transactions.sort(key=lambda row: row[0], reverse=True)  # 거래 시간으로 내림차순 정렬
        for transaction in transactions:
            transaction = list(transaction)
            transaction[0] = datetime2utcstr(transaction[0])
            detail["billing"]["transactions"].append(
                dict(zip(transaction_fields, transaction))
            )
    elif currency == "USD":
        transactions = await db.exec(
            template=db.Template(table="paypal_billings").select_query(
                "transaction_time", "order_name", "total_amount", **cond_kwargs
            )
        )
        transactions.sort(key=lambda row: row[0], reverse=True)  # 거래 시간으로 내림차순 정렬
        for transaction in transactions:
            transaction = list(transaction)
            transaction[0] = datetime2utcstr(transaction[0])
            transaction.append("PayPal")  # method -> PayPal
            detail["billing"]["transactions"].append(
                dict(zip(transaction_fields, transaction))
            )
    return detail


@router.private.delete()
async def delete_user(user=router.private.auth):
    """DB와 Cognito에서 유저 삭제 (회원탈퇴)"""
    await db.exec(
        "DELETE FROM users WHERE id={user_id};",
        """
        UPDATE signup_histories 
        SET user_deleted = CURRENT_TIMESTAMP 
        WHERE user_id={user_id};
        """,
        params={"user_id": user["id"]},
    )
    await run_async(
        cognito.delete_user,
        AccessToken=user["cognito_access_token"],
    )
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
    if await db.user_exists(email):
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
    user=router.private.auth,
):
    """유저 이름 변경"""
    await db.exec(
        "UPDATE users SET name={user_name} WHERE id={user_id}",
        params={"user_name": new_name, "user_id": user["id"]},
    )
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
    if not await db.user_exists(email):
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


class PayPalSubscription(BaseModel):
    subscription: constr(min_length=1)
    next_billing: constr(min_length=1)  # UTC 시간대 ISO 8601: "%Y-%m-%dT%H:%M:%S.000Z"


class MembershipChangeRequest(BaseModel):
    new_membership: constr(min_length=1)
    paypal: PayPalSubscription | None = None


@router.private.patch("/membership")
async def change_membership(item: MembershipChangeRequest, user=router.private.auth):
    """
    - 맴버십을 변경합니다.
    - new_membership: 변경 후 맴버십
    - paypal_subscription_id[Optional]: USD 통화를 사용하는 PayPal 유저인 경우 새로운 PayPal 구독 ID를 발급받아 입력
        - 구독 생성 시 GET /api/paypal/membership-change-subscription-start-time 를 사용하세요
    - Response: 조정된 다음 청구일시
    """
    (
        current_membership,
        currency,
        origin_billing_date,
        base_billing_date,
        current_billing_date,
        next_billing_date,
    ) = await db.exec(
        template=db.Template(table="users").select_query(
            "membership",
            "currency",
            "origin_billing_date",
            "base_billing_date",
            "current_billing_date",
            "next_billing_date",
            where={"id": user["id"]},
            limit=1,
        ),
        embed=True,
    )

    new_membership = item.new_membership
    if current_membership == new_membership or new_membership not in MEMBERSHIP:
        raise HTTPException(
            status_code=409,
            detail=f"The {new_membership} membership is either identical to the already set value or invalid",
        )

    update_query_tosspayments = """
        UPDATE users 
        SET membership={new_membership}, 
            base_billing_date={base_billing_date},
            next_billing_date={next_billing}
        WHERE id={user_id};"""
    update_query_paypal = """
        UPDATE users 
        SET membership={new_membership}, 
            base_billing_date={base_billing_date},
            next_billing_date={next_billing},
            paypal_subscription_id={subscription_id}
        WHERE id={user_id};"""  # paypal_subscription_id 업데이트 필요

    if current_billing_date is None:  # 결제가 필요 없는 계정이므로 맴버십만 바꾸면 됌
        await db.exec(
            "UPDATE users SET membership={new_membership} WHERE id={user_id};",
            params={"new_membership": new_membership, "user_id": user["id"]},
        )
        adjusted_next_billing = next_billing_date
    elif origin_billing_date == base_billing_date:  # 이전에 결제된 맴버십을 다른것으로 변경하는 경우
        if currency == "USD" and item.paypal:
            # PayPal -> 다음 청구 날짜는 PayPal이 통지한 날짜로 해야 함
            adjusted_next_billing = utcstr2datetime(item.paypal.next_billing)
            await db.exec(
                update_query_paypal,
                params={
                    "new_membership": new_membership,
                    "base_billing_date": adjusted_next_billing,
                    "next_billing": adjusted_next_billing,
                    "user_id": user["id"],
                    "subscription_id": item.paypal.subscription,
                },
            )
        elif currency == "KRW":
            # Tosspayments -> 다음 청구 날짜 직접 계산
            adjusted_next_billing = calc_next_billing_date_adjust_membership_change(
                base_billing=base_billing_date,
                current_billing=current_billing_date,
                current_membership=current_membership,
                new_membership=new_membership,
                change_day=datetime.now(),
                currency=currency,
            )
            await db.exec(
                update_query_tosspayments,
                params={
                    "new_membership": new_membership,
                    "base_billing_date": adjusted_next_billing,
                    "next_billing": adjusted_next_billing,
                    "user_id": user["id"],
                },
            )
    else:  # 결제가 이루어지기 전에, 기존 맴버십으로 롤백하는 경우
        if currency == "USD" and item.paypal:
            adjusted_next_billing = utcstr2datetime(item.paypal.next_billing)
            await db.exec(
                update_query_paypal,
                params={
                    "new_membership": new_membership,
                    "base_billing_date": origin_billing_date,
                    "next_billing": adjusted_next_billing,
                    "user_id": user["id"],
                    "subscription_id": item.paypal.subscription,
                },
            )
        elif currency == "KRW":
            adjusted_next_billing = calc_next_billing_date(
                base=origin_billing_date, current=current_billing_date
            )
            await db.exec(
                update_query_tosspayments,
                params={
                    "new_membership": new_membership,
                    "base_billing_date": origin_billing_date,
                    "next_billing": adjusted_next_billing,
                    "user_id": user["id"],
                },
            )

    return {"adjusted_next_billing": datetime2utcstr(adjusted_next_billing)}


class PaymentMethodInfo(BaseModel):
    tosspayments: TosspaymentsBillingInfo | None = None
    paypal: PaypalBillingInfo | None = None


@router.private.patch("/payment-method")
async def change_payment_method(item: PaymentMethodInfo, user=router.private.auth):
    """결제수단을 변경합니다. PG사 변경은 불가능합니다."""
    currency, *_ = await db.exec(
        "SELECT currency FROM users WHERE id={user_id}",
        params={"user_id": user["id"]},
        embed=True,
    )
    if currency == "KRW" and item.tosspayments:
        tosspayments = TosspaymentsBilling(user_id=user["id"])
        try:
            billing_key = await tosspayments.get_billing_key(
                item.tosspayments.card_number,
                item.tosspayments.expiration_year,
                item.tosspayments.expiration_month,
                item.tosspayments.owner_id,
            )
            payment_info = await tosspayments.billing(
                billing_key, amount=100, order_name="Payment method confirmation"
            )  # 100원 결제
            await TosspaymentsAPI(
                f"/v1/payments/{payment_info['paymentKey']}/cancel"
            ).post(
                {"cancelReason": "Confirmed"}  # 100원 환불
            )
        except httpx.HTTPStatusError:
            raise HTTPException(
                status_code=402,
                detail=f"[Tosspayments] Your payment information is incorrect.",
            )
        await db.exec(
            "UPDATE users SET tosspayments_billing_key={billing_key} WHERE id={user_id}",
            params={"billing_key": billing_key, "user_id": user["id"]},
        )
    elif currency == "USD" and item.paypal:  # 페이팔 빌링
        try:
            subscription = await pooling(
                target=PayPalAPI(  # subscription 유효성 확인
                    f"/v1/billing/subscriptions/{item.paypal.subscription}"
                ).get,
                inspecter=lambda subscription: subscription["status"] == "ACTIVE",
                timeout=30,  # 조건이 만족될때까지 최대 30초 재시도합니다.
            )  # timeout이 초과되어도 조건이 만족되지 않으면 AssertionError
            next_billing = utcstr2datetime(
                subscription["billing_info"]["next_billing_time"]
            )
        except (AssertionError, httpx.HTTPStatusError):
            raise HTTPException(
                status_code=402,
                detail=f"[PayPal] Your subscription status in paypal server is incorrect",
            )
        await db.exec(
            """
            UPDATE users SET paypal_subscription_id={subscription}, 
                next_billing_date={next_billing} 
            WHERE id={user_id}
            """,
            params={
                "subscription": item.paypal.subscription,
                "next_billing": next_billing,
                "user_id": user["id"],
            },
        )
    else:
        raise HTTPException(
            status_code=409,
            detail="Payment info doesn't match user's currency or user has no payment details",
        )
    return {"message": "Payment method updated"}
