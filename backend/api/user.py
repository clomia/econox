from calendar import monthrange
from datetime import datetime

import boto3
import psycopg
import ipinfo
from fastapi import HTTPException, Request, Body
from fastapi.responses import Response
from pydantic import BaseModel

from backend import db
from backend.api import router
from backend.system import SECRETS, log

API_PREFIX = "user"

region = "us-east-1"
cognito = boto3.client("cognito-idp", region_name=region)


@router.post("/user/cognito", tags=[API_PREFIX])
async def create_cognito_user(email: str = Body(...), password: str = Body(...)):
    try:
        result = cognito.sign_up(
            ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
            Username=email,
            Password=password,
            UserAttributes=[{"Name": "email", "Value": email}],
        )
    except cognito.exceptions.UsernameExistsException:
        if db.execute_query(f"SELECT 1 FROM users WHERE email='{email}' LIMIT 1;"):
            raise HTTPException(status_code=409)
        else:
            cognito.admin_delete_user(
                UserPoolId=SECRETS["COGNITO_USER_POOL_ID"], Username=email
            )
            result = cognito.sign_up(
                ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
                Username=email,
                Password=password,
                UserAttributes=[{"Name": "email", "Value": email}],
            )
    except (
        cognito.exceptions.InvalidParameterException,
        cognito.exceptions.CodeDeliveryFailureException,
    ):  # 이메일 인증을 진행할 수 없습니다!
        raise HTTPException(status_code=400)
    return {"user_id": result["UserSub"]}


class UserSignup(BaseModel):
    cognito_id: str
    email: str
    phone: str
    membership: str
    currency: str
    tosspayments: dict[str, str] | None = None
    paypal: dict[str, str] | None = None


@router.post("/user", tags=[API_PREFIX])
async def signup(item: UserSignup):
    try:
        cognito_user = cognito.admin_get_user(
            UserPoolId=SECRETS["COGNITO_USER_POOL_ID"], Username=item.email
        )
        print(cognito_user)
    except cognito.exceptions.UserNotFoundException:
        raise HTTPException(status_code=409, detail="cognito user not found")
    if cognito_user["UserStatus"] != "CONFIRMED":
        raise HTTPException(status_code=401, detail="cognito user is not confirmed")
    if cognito_user["Username"] != item.cognito_id:
        raise HTTPException(status_code=409, detail="invalid cognito id")

    scan_history = f"""
        SELECT 1 FROM signup_history 
        WHERE email='{item.email}' or phone='{item.phone}'
        LIMIT 1;
    """
    signup_history = db.execute_query(scan_history)  # 회원가입 내역이 있다면 결제정보 필요함
    if signup_history and not (item.tosspayments or item.paypal):
        raise HTTPException(status_code=402, detail="billing information required")

    # 다음달 동일 일시를 구하되 마지막 일보다 크면 마지막 일로 대체
    now = datetime.now()
    year, month = (now.year + 1, 1) if now.month == 12 else (now.year, now.month + 1)
    day = min(now.day, monthrange(year, month)[1])
    membership_expiration = datetime(year, month, day, now.hour, now.minute, now.second)

    insert_user = f"""
    INSERT INTO users (id, email, name, phone, membership, membership_expiration, 
        currency, tosspayments_billing_key, paypal_token, paypal_subscription_id,
        billing_date, billing_time) 
    VALUES (
        '{item.cognito_id}', 
        '{item.email}', 
        '{item.email.split("@")[0]}', 
        '{item.phone}', 
        '{item.membership}', 
        '{membership_expiration.strftime('%Y-%m-%d %H:%M:%S')}', 
        '{item.currency}', 
        {f"'{item.tosspayments['billingKey']}'" if item.tosspayments else "NULL"},
        {f"'{item.paypal['facilitatorAccessToken']}'" if item.paypal else "NULL"}, 
        {f"'{item.paypal['subscriptionId']}'" if item.paypal else "NULL"},
        {now.day},
        '{now.strftime('%H:%M:%S')}'
    );
    """
    try:
        db.execute_query(insert_user)
    except psycopg.errors.UniqueViolation:  # email colume is unique
        raise HTTPException(status_code=409, detail="Email is already in used")

    insert_signup_history = f"""
    INSERT INTO signup_history (email, phone) 
    VALUES ('{item.email}', '{item.phone}')
    """
    db.execute_query(insert_signup_history)
    return {"benefit": not bool(signup_history)}  # 첫 회원가입 혜택 여부


@router.get("/user/country", tags=[API_PREFIX])
async def get_user_country(request: Request):
    handler = ipinfo.getHandlerAsync(SECRETS["IPINFO_API_KEY"])
    try:
        client_info = await handler.getDetails(request.client.host)
        return {"country": client_info.country, "timezone": client_info.timezone}
    except AttributeError:  # localhost(테스트)인 경우
        default = {"country": "KR", "timezone": "Asia/Seoul"}
        log.warning(
            "GET /user/country"
            f"\n국가 정보 취득에 실패했습니다. 기본값을 응답합니다."
            f"\nIP: {request.client.host} , 응답된 기본값: {default}"
        )
        return default
    finally:
        await handler.deinit()
