import time
import secrets
import threading
from pathlib import PosixPath

import boto3
from fastapi import Body, HTTPException
from fastapi.responses import Response

from backend.api import router
from backend.system import db_exec_query, run_async
from backend.system import SECRETS, EFS_VOLUME_PATH

API_PREFIX = "auth"
cognito = boto3.client("cognito-idp")


@router.post("/auth/user", tags=[API_PREFIX])
async def login(email: str = Body(...), password: str = Body(...)):
    if not await db_exec_query(f"SELECT 1 FROM users WHERE email='{email}' LIMIT 1;"):
        raise HTTPException(status_code=404, detail="User does not exist")
    try:
        await run_async(
            cognito.admin_user_global_sign_out,
            UserPoolId=SECRETS["COGNITO_USER_POOL_ID"],
            Username=email,
        )  # 유저에게 발급된 refresh token 전부 무효화, 한 계정이 여러곳에서 동시에 사용되는걸 막는다.
    except cognito.exceptions.UserNotFoundException:  # 정상적으로 회원가입이 되었다면 이 에러는 절대 안난다.
        raise HTTPException(status_code=409, detail="Cognito User does not exist")
    try:
        result = await run_async(
            cognito.initiate_auth,
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": email, "PASSWORD": password},
            ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
        )
    except cognito.exceptions.NotAuthorizedException:
        raise HTTPException(status_code=401, detail="Invalid password")
    return {
        "cognito_id_token": result["AuthenticationResult"]["IdToken"],
        "cognito_access_token": result["AuthenticationResult"]["AccessToken"],
        "cognito_refresh_token": result["AuthenticationResult"]["RefreshToken"],
    }


@router.post("/auth/cognito-refresh-token", tags=[API_PREFIX])
async def cognito_token_refresh(cognito_refresh_token: str = Body(..., embed=True)):
    try:
        result = await run_async(
            cognito.initiate_auth,
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={"REFRESH_TOKEN": cognito_refresh_token},
            ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
        )
    except cognito.exceptions.NotAuthorizedException:
        raise HTTPException(status_code=401, detail="Invalid token")
    return {
        "cognito_id_token": result["AuthenticationResult"]["IdToken"],
        "cognito_access_token": result["AuthenticationResult"]["AccessToken"],
    }


# ------------------ for phone authentication ------------------
PHONE_CONFIRMATION_CODE_PATH = EFS_VOLUME_PATH / "phone_confirmation_code"
PHONE_CONFIRMATION_CODE_PATH.mkdir(parents=True, exist_ok=True)


@router.post("/auth/phone", tags=[API_PREFIX])
async def create_phone_confirmation(phone=Body(..., embed=True)):
    target_path: PosixPath = PHONE_CONFIRMATION_CODE_PATH / phone
    issued_code = f"{secrets.randbelow(10**6):06}"
    target_path.write_text(issued_code)
    sns = boto3.client("sns")
    resp = await run_async(
        sns.publish,
        PhoneNumber=phone,
        Message=f"ECONOX confirmation code: {issued_code}",
    )
    assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200

    def code_expiration():
        time.sleep(180)  # 3분 뒤 코드 만료
        target_path.unlink(missing_ok=True)

    threading.Thread(target=code_expiration).start()
    return Response(status_code=200, content="Code transfer request successful")


@router.post("/auth/phone/confirm", tags=[API_PREFIX])
async def phone_confirmation(
    phone: str = Body(...), confirmation_code: str = Body(...)
):
    target_path = PHONE_CONFIRMATION_CODE_PATH / phone
    if not target_path.exists():  # 코드 만료
        raise HTTPException(
            status_code=401, detail="This confirmation has already expired."
        )
    elif target_path.read_text() == confirmation_code:
        return Response(status_code=200, content="confirmed")
    else:
        raise HTTPException(status_code=409, detail="Invalid code")


@router.post("/auth/email", tags=[API_PREFIX])
async def cognito_resend_confirmation_code(email: str = Body(..., embed=True)):
    await run_async(  # 이메일 잘못되도 에러 안나서 예외처리할게 없음..
        cognito.resend_confirmation_code,
        ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
        Username=email,
    )
    return Response(status_code="Code transfer requested")


@router.post("/auth/email/confirm", tags=[API_PREFIX])
async def cognito_confirm_sign_up(
    email: str = Body(...), confirmation_code: str = Body(...)
):
    try:
        await run_async(
            cognito.confirm_sign_up,
            ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
            Username=email,
            ConfirmationCode=confirmation_code,
        )
    except cognito.exceptions.CodeMismatchException:
        raise HTTPException(status_code=409, detail="Invalid code")
    except cognito.exceptions.ExpiredCodeException:
        raise HTTPException(status_code=401, detail="Expired code")
    except cognito.exceptions.LimitExceededException:
        raise HTTPException(status_code=429, detail="Too many requests")
    except cognito.exceptions.NotAuthorizedException:
        return Response(status_code=202, content="Email already confirmed")
    return Response(status_code=200, content="Confirmed")


@router.post("/auth/is-reregistration", tags=[API_PREFIX])
async def check_for_is_reregistration(email: str = Body(...), phone: str = Body(...)):
    scan_history = f"""
        SELECT 1 FROM signup_history 
        WHERE email='{email}' or phone='{phone}'
        LIMIT 1;
    """
    signup_history = await db_exec_query(scan_history)
    return {"reregistration": bool(signup_history)}
