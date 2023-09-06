""" /api/user """

import asyncio
from uuid import uuid4
from typing import Literal
from datetime import datetime
from calendar import monthrange

import boto3
import ipinfo
import psycopg
from pydantic import BaseModel, constr
from fastapi import HTTPException, Request, Body

from backend.http import APIRouter, TosspaymentsAPI, PayPalAPI
from backend.system import SECRETS, db_exec_query, run_async, log, membership


router = APIRouter("user")
cognito = boto3.client("cognito-idp")


class TosspaymentsBillingInfo(BaseModel):
    key: constr(min_length=1)  # billing key


class PaypalBillingInfo(BaseModel):
    order: constr(min_length=1)  # order id
    token: constr(min_length=1)
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
    - Response: 첫 회원가입 혜택 여부
    """
    insert_queries = []
    try:
        cognito_user = await run_async(
            cognito.admin_get_user,
            UserPoolId=SECRETS["COGNITO_USER_POOL_ID"],
            Username=item.email,
        )
        cognito_user_id = cognito_user["Username"]
    except cognito.exceptions.UserNotFoundException:
        raise HTTPException(status_code=409, detail="Cognito user not found")
    if cognito_user["UserStatus"] != "CONFIRMED":
        raise HTTPException(status_code=401, detail="Cognito user is not confirmed")

    now = datetime.now()  # 다음달 동일 일시를 구하되 마지막 일보다 크면 마지막 일로 대체
    year, month = (now.year + 1, 1) if now.month == 12 else (now.year, now.month + 1)
    day = min(now.day, monthrange(year, month)[1])
    membership_expiration = datetime(year, month, day, now.hour, now.minute, now.second)

    insert_queries.append(
        f"""
    INSERT INTO users (id, email, name, phone, membership, membership_expiration, 
        currency, tosspayments_billing_key, paypal_token, paypal_subscription_id,
        billing_date, billing_time) 
    VALUES (
        '{cognito_user_id}', 
        '{item.email}', 
        '{item.email.split("@")[0]}', 
        '{item.phone}', 
        '{item.membership}', 
        '{membership_expiration.strftime('%Y-%m-%d %H:%M:%S')}', 
        '{item.currency}', 
        {f"'{item.tosspayments.key}'" if item.tosspayments else "NULL"},
        {f"'{item.paypal.token}'" if item.paypal else "NULL"}, 
        {f"'{item.paypal.subscription}'" if item.paypal else "NULL"},
        {now.day},
        '{now.strftime('%H:%M:%S')}'
    );
    """
    )
    insert_queries.append(
        f"""
    INSERT INTO signup_histories (email, phone) 
    VALUES ('{item.email}', '{item.phone}');
    """
    )

    scan_history = f"""
        SELECT 1 FROM signup_histories 
        WHERE email='{item.email}' or phone='{item.phone}'
        LIMIT 1;
    """  # 회원가입 내역이 있다면 결제정보 필요함
    signup_histories = await db_exec_query(scan_history)
    if signup_histories:
        if item.currency == "KRW" and item.tosspayments:  # 대금 결제 수행
            resp = await TosspaymentsAPI(f"/v1/billing/{item.tosspayments.key}").post(
                {
                    "customerKey": cognito_user_id,
                    "orderId": str(uuid4()),
                    "orderName": f"ECONOX {item.membership.capitalize()} Membership",
                    "amount": membership[item.membership][item.currency],
                    "customerEmail": item.email,
                }
            )
            insert_queries.append(
                f"""
            INSERT INTO tosspayments_billings (user_id, order_id, payment_key, 
                order_name, total_amount, supply_price, vat, card_issuer, 
                card_acquirer, card_number_masked, card_approve_number, card_type, 
                card_owner_type, receipt_url) 
            VALUES (
                '{cognito_user_id}', 
                '{resp["orderId"]}', 
                '{resp["paymentKey"]}', 
                '{resp["orderName"]}', 
                '{resp["totalAmount"]}', 
                '{resp["suppliedAmount"]}', 
                '{resp["vat"]}', 
                '{resp["card"]["issuerCode"]}',
                '{resp["card"]["acquirerCode"]}',
                '{resp["card"]["number"]}',
                '{resp["card"]["approveNo"]}',
                '{resp["card"]["cardType"]}',
                '{resp["card"]["ownerType"]}',
                '{resp["receipt"]["url"]}'
            );
            """
            )
        elif item.currency == "USD" and item.paypal:
            order, subscription = asyncio.gather(
                PayPalAPI(f"/v2/checkout/orders/{item.paypal.order}").get(),
                PayPalAPI(
                    f"/v1/billing/subscriptions/{item.paypal.subscription}"
                ).get(),
            )
            assert order["status"] == "APPROVED"
            assert subscription["status"] == "ACTIVE"
        else:
            raise HTTPException(
                status_code=402,
                detail="Correct billing information is required.",
            )

    try:
        await db_exec_query(*insert_queries)
    except psycopg.errors.UniqueViolation:  # email colume is unique
        raise HTTPException(status_code=409, detail="Email is already in used")
    return {"first_signup_benefit": not signup_histories}  # 첫 회원가입 혜택 여부


@router.public.post("/cognito")
async def create_cognito_user(
    email: str = Body(..., min_length=1),
    password: str = Body(..., min_length=1),
):
    """
    - AWS Cognito에 유저 생성 & 이메일로 인증코드 전송
    - /api/auth/email/confirm 엔드포인트로 해당 인증코드를 인증해야 함
    - Response: Cognito에서 생성된 유저 ID
    """
    if await db_exec_query(f"SELECT 1 FROM users WHERE email='{email}' LIMIT 1;"):
        raise HTTPException(status_code=409, detail="Email is already in used")
    try:
        result = await run_async(
            cognito.sign_up,
            ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
            Username=email,
            Password=password,
            UserAttributes=[{"Name": "email", "Value": email}],
        )
    except cognito.exceptions.UsernameExistsException:
        # cognito에 유저가 생성되었지만 회원가입이 완료되지 않은 상태이므로 cognito 유저 삭제 후 재시도
        await run_async(
            cognito.admin_delete_user,
            UserPoolId=SECRETS["COGNITO_USER_POOL_ID"],
            Username=email,
        )
        result = await run_async(
            cognito.sign_up,
            ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
            Username=email,
            Password=password,
            UserAttributes=[{"Name": "email", "Value": email}],
        )
    except (
        cognito.exceptions.InvalidParameterException,
        cognito.exceptions.CodeDeliveryFailureException,
    ):
        raise HTTPException(status_code=400, detail="Email is not valid")
    return {"cognito_id": result["UserSub"]}


@router.public.get("/country")
async def get_user_country(request: Request):
    """
    - HTTP 요청이 이루어진 국가를 응답합니다.
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
            "GET /user/country"
            f"\n국가 정보 취득에 실패했습니다. 기본값을 응답합니다."
            f"\nIP: {request.client.host} , 응답된 기본값: {default}"
        )
        return default
    finally:
        await handler.deinit()


@router.private.patch("/name")
async def change_user_name(
    new_name: str = Body(..., min_length=1, embed=True),
    user=router.private.auth,
):
    """
    - 유저 이름 변경
    """
    await db_exec_query(f"UPDATE users SET name='{new_name}' WHERE id='{user['id']}'")
    return {"message": "Changed successfully"}
