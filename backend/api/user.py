""" /api/user """
import asyncio
from typing import Literal
from datetime import datetime
from functools import partial

import httpx
import boto3
import ipinfo
import psycopg
from pydantic import BaseModel, constr
from fastapi import HTTPException, Request, Body

from backend.math import calculate_membership_expiry
from backend.http import APIRouter, TosspaymentsAPI, PayPalAPI, idempotent_retries
from backend.system import SECRETS, db_exec_query, run_async, log, membership


router = APIRouter("user")
cognito = boto3.client("cognito-idp")


class TosspaymentsBillingInfo(BaseModel):
    card_number: constr(min_length=1)
    expiration_year: constr(min_length=1)
    expiration_month: constr(min_length=1)
    owner_id: constr(min_length=1)


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
    - 결제 정보가 누락되거나 잘못된 경우 402 응답
    - Response: 첫 회원가입 혜택 여부
    """

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

    insert_queries = []  # DB 쿼리 실행 리스트

    scan_history = f"""
        SELECT 1 FROM signup_histories 
        WHERE email='{item.email}' or phone='{item.phone}'
        LIMIT 1;
    """  # 회원가입 내역이 있다면 결제정보 필요함
    signup_histories = await db_exec_query(scan_history)
    if signup_histories:
        if item.currency == "KRW" and item.tosspayments:  # 토스페이먼츠 빌링
            tosspayments_billing: dict = await TosspaymentsAPI.create_billing(
                cognito_user_id,
                item.tosspayments.card_number,
                item.tosspayments.expiration_year,
                item.tosspayments.expiration_month,
                item.tosspayments.owner_id,
                item.email,
                order_name=f"Econox {item.membership.capitalize()} Membership",
                amount=membership[item.membership][item.currency],
            )
            payment = tosspayments_billing["payment"]
            insert_queries.append(
                f"""
            INSERT INTO tosspayments_billings (user_id, order_id, payment_key, 
                order_name, total_amount, supply_price, vat, card_issuer, 
                card_acquirer, card_number_masked, card_approve_number, card_type, 
                card_owner_type, receipt_url) 
            VALUES (
                '{cognito_user_id}', 
                '{payment["orderId"]}', 
                '{payment["paymentKey"]}', 
                '{payment["orderName"]}', 
                '{payment["totalAmount"]}', 
                '{payment["suppliedAmount"]}', 
                '{payment["vat"]}', 
                '{payment["card"]["issuerCode"]}',
                '{payment["card"]["acquirerCode"]}',
                '{payment["card"]["number"]}',
                '{payment["card"]["approveNo"]}',
                '{payment["card"]["cardType"]}',
                '{payment["card"]["ownerType"]}',
                '{payment["receipt"]["url"]}'
            );
            """
            )
        elif item.currency == "USD" and item.paypal:  # 페이팔 빌링
            # -- 빌링 정보 검사 --
            order_detail_api = f"/v2/checkout/orders/{item.paypal.order}"
            subscription_detail_api = (
                f"/v1/billing/subscriptions/{item.paypal.subscription}"
            )
            try:
                await idempotent_retries(
                    target=partial(
                        asyncio.gather,  # 주문과 구독 정보를 가져옵니다.
                        PayPalAPI(order_detail_api).get(),
                        PayPalAPI(subscription_detail_api).get(),
                    ),
                    inspecter=(  # 주문 정보와 구독 정보가 완료상태인지 확인합니다.
                        lambda results: results[0]["status"] != "APPROVED"
                        or results[1]["status"] == "ACTIVE"
                    ),
                    timeout=30,  # 조건이 만족될때까지 최대 30초 재시도합니다.
                )  # timeout이 초과되어도 조건이 만족되지 않으면 AssertionError
            except (httpx.HTTPStatusError, AssertionError) as e:
                raise HTTPException(
                    status_code=402,
                    detail=f"PayPal does not have subscription and order information\nResponse detail: {e}",
                )
        else:
            raise HTTPException(
                status_code=402,
                detail="Correct billing information is required",
            )

    now = datetime.now()
    membership_expiration = calculate_membership_expiry(start=now)
    create_user = f"""
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
        {f"'{tosspayments_billing['key']}'" if item.tosspayments else "NULL"},
        {f"'{item.paypal.token}'" if item.paypal else "NULL"}, 
        {f"'{item.paypal.subscription}'" if item.paypal else "NULL"},
        {now.day},
        '{now.strftime('%H:%M:%S')}'
    );
    """  # 유저 생성 쿼리가 가장 먼저 실행되어야 함
    insert_queries.insert(0, create_user)
    insert_queries.append(
        f"""
    INSERT INTO signup_histories (email, phone) 
    VALUES ('{item.email}', '{item.phone}');
    """
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
