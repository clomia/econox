import time
import secrets
import threading
from pathlib import PosixPath

import boto3
from fastapi import Body, HTTPException
from fastapi.responses import Response

from backend.http import Router
from backend.system import db_exec_query, run_async
from backend.system import SECRETS, EFS_VOLUME_PATH

router = Router("auth")
cognito = boto3.client("cognito-idp")


@router.public.post("/auth/user")
async def login(email: str = Body(...), password: str = Body(...)):
    if not await db_exec_query(f"SELECT 1 FROM users WHERE email='{email}' LIMIT 1;"):
        raise HTTPException(status_code=404, detail="user does not exist")

    # ========== 이전에 발급된 모든 refresh 토큰 무효화 요청 전송 ==========
    try:
        await run_async(
            cognito.admin_user_global_sign_out,
            UserPoolId=SECRETS["COGNITO_USER_POOL_ID"],
            Username=email,
        )  # 유저에게 발급된 refresh token 전부 무효화, 한 계정이 여러곳에서 동시에 사용되는걸 막는다.
    except cognito.exceptions.UserNotFoundException:  # 정상적으로 회원가입이 되었다면 이 에러는 절대 안난다.
        raise HTTPException(status_code=409, detail="cognito User does not exist")

    # ========== refresh 토큰 무효화 요청이 완료되길 기다린(polling) 다음 유일한 refresh 토큰 생성 ==========
    while True:  # 모든 refresh 토큰이 무효화될때까지 반복됨
        try:
            auth = await run_async(  # 1. refresh 토큰 발급
                cognito.initiate_auth,
                AuthFlow="USER_PASSWORD_AUTH",
                AuthParameters={"USERNAME": email, "PASSWORD": password},
                ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
            )
        except cognito.exceptions.NotAuthorizedException:
            raise HTTPException(status_code=401, detail="invalid password")
        id_token = auth["AuthenticationResult"]["IdToken"]
        access_token = auth["AuthenticationResult"]["AccessToken"]
        refresh_token = auth["AuthenticationResult"]["RefreshToken"]
        try:
            await run_async(  # 2. 발급된 refresh 토큰이 유효한지 검사
                cognito.initiate_auth,
                AuthFlow="REFRESH_TOKEN_AUTH",
                AuthParameters={"REFRESH_TOKEN": refresh_token},
                ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
            )
        except cognito.exceptions.NotAuthorizedException:
            continue  # 3. 유효하지 않다면 재시도 (polling...)
        else:
            break  # 4. 유일한 refresh 토큰 획득 성공!
    return {
        "cognito_token": id_token + "|" + access_token,
        "cognito_refresh_token": refresh_token,
    }


@router.public.post("/auth/cognito-refresh-token")
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
    id_token = result["AuthenticationResult"]["IdToken"]
    access_token = result["AuthenticationResult"]["AccessToken"]
    return {"cognito_token": id_token + "|" + access_token}


# ------------------ for phone authentication ------------------
PHONE_CONFIRMATION_CODE_PATH = EFS_VOLUME_PATH / "phone_confirmation_code"
PHONE_CONFIRMATION_CODE_PATH.mkdir(parents=True, exist_ok=True)


@router.public.post("/auth/phone")
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


@router.public.post("/auth/phone/confirm")
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
        raise HTTPException(status_code=409, detail="invalid code")


@router.public.post("/auth/email")
async def cognito_resend_confirmation_code(email: str = Body(..., embed=True)):
    await run_async(  # 이메일 잘못되도 에러 안나서 예외처리할게 없음..
        cognito.resend_confirmation_code,
        ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
        Username=email,
    )
    return Response(status_code="code transfer requested")


@router.public.post("/auth/email/confirm")
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
        raise HTTPException(status_code=409, detail="invalid code")
    except cognito.exceptions.ExpiredCodeException:
        raise HTTPException(status_code=401, detail="expired code")
    except cognito.exceptions.LimitExceededException:
        raise HTTPException(status_code=429, detail="too many requests")
    except cognito.exceptions.NotAuthorizedException:
        return Response(status_code=202, content="email already confirmed")
    return Response(status_code=200, content="confirmed")


@router.public.post("/auth/is-reregistration")
async def check_is_reregistration(email: str = Body(...), phone: str = Body(...)):
    scan_history = f"""
        SELECT 1 FROM signup_history 
        WHERE email='{email}' or phone='{phone}'
        LIMIT 1;
    """
    signup_history = await db_exec_query(scan_history)
    return {"reregistration": bool(signup_history)}
