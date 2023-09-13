""" /api/auth """
import time
import secrets
import threading
from pathlib import PosixPath

import boto3
from fastapi import Body, HTTPException

from backend import db
from backend.http import APIRouter
from backend.system import run_async
from backend.system import SECRETS, EFS_VOLUME_PATH

router = APIRouter("auth")
cognito = boto3.client("cognito-idp")


@router.public.post("/user")
async def login(
    email: str = Body(..., min_length=1),
    password: str = Body(..., min_length=1),
):
    """
    - 로그인 정보로 유저 인증
    - Response: 인증 토큰 & 갱신용 토큰
    """

    if not await db.user_exists(email):
        raise HTTPException(status_code=404, detail="User does not exist")
    # ========== 이전에 발급된 모든 refresh 토큰 무효화 요청 ==========
    try:
        await run_async(
            cognito.admin_user_global_sign_out,
            UserPoolId=SECRETS["COGNITO_USER_POOL_ID"],
            Username=email,
        )  # 유저에게 발급된 refresh token 전부 무효화, 한 계정이 여러곳에서 동시에 사용되는걸 막는다.
    except cognito.exceptions.UserNotFoundException:  # 정상적으로 회원가입이 되었다면 이 에러는 절대 안난다.
        raise HTTPException(status_code=409, detail="Cognito user does not exist")
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
            raise HTTPException(status_code=401, detail="Invalid password")
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


# ------------------ for phone authentication ------------------
PHONE_CONFIRM_CODE_PATH = EFS_VOLUME_PATH / "phone_confirm_code"
PHONE_CONFIRM_CODE_PATH.mkdir(parents=True, exist_ok=True)


@router.public.post("/phone")
async def create_phone_confirmation(phone: str = Body(..., min_length=1, embed=True)):
    """
    - 전화번호로 인증코드 전송
    - 3분 뒤 인증코드 만료
    - POST /api/auth/phone/confirm 엔드포인트로 해당 인증코드를 인증해야 함
    """
    target_path: PosixPath = PHONE_CONFIRM_CODE_PATH / phone
    issued_code = f"{secrets.randbelow(10**6):06}"
    target_path.write_text(issued_code)
    sns = boto3.client("sns")
    try:
        resp = await run_async(
            sns.publish,
            PhoneNumber=phone,
            Message=f"Econox confirmation code: {issued_code}",
        )
        assert resp["ResponseMetadata"]["HTTPStatusCode"] == 200
    except sns.exceptions.InvalidParameterException:
        raise HTTPException(status_code=409, detail="Phone number is not valid")

    def code_expiration():
        time.sleep(180)  # 3분 뒤 코드 만료
        target_path.unlink(missing_ok=True)

    threading.Thread(target=code_expiration).start()
    return {"message": "Code transfer request successful"}


@router.public.post("/phone/confirm")
async def phone_confirmation(
    phone: str = Body(..., min_length=1),
    confirm_code: str = Body(..., min_length=1),
):
    """
    - 전송된 인증코드로 전화번호 인증
    - POST /api/auth/phone 엔드포인트로 인증코드를 전송할 수 있음
    """
    target_path = PHONE_CONFIRM_CODE_PATH / phone
    if not target_path.exists():  # 코드 만료
        raise HTTPException(
            status_code=401, detail="This confirmation has already expired."
        )
    elif target_path.read_text() == confirm_code:
        return {"message": "Confirmed"}
    else:
        raise HTTPException(status_code=409, detail="Invalid code")


@router.public.post("/email")
async def cognito_resend_confirm_code(email: str = Body(..., min_length=1, embed=True)):
    """
    - 이메일로 인증코드 전송
    - AWS Cognito user pool에 존재하는 이메일이어야 함
        - Cognito 유저가 없는 경우 /api/user/cognito 엔드포인트를 사용해야 함
    - POST /api/auth/email/confirm 엔드포인트로 해당 인증코드를 인증해야 함
    """
    try:
        await run_async(
            cognito.resend_confirmation_code,
            ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
            Username=email,
        )
    except cognito.exceptions.LimitExceededException:
        raise HTTPException(status_code=429, detail="Too many requests")
    else:
        return {"message": "Code transfer requested"}


@router.public.post("/email/confirm")
async def cognito_confirm_sign_up(
    email: str = Body(..., min_length=1),
    confirm_code: str = Body(..., min_length=1),
):
    """
    - 전송된 인증코드로 이메일 인증
    - POST /api/user/cognito 혹은 POST /api/auth/email 엔드포인트로 인증코드를 전송할 수 있음
    """
    try:
        await run_async(
            cognito.confirm_sign_up,
            ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
            Username=email,
            ConfirmationCode=confirm_code,
        )
    except cognito.exceptions.CodeMismatchException:
        raise HTTPException(status_code=409, detail="Invalid code")
    except cognito.exceptions.ExpiredCodeException:
        raise HTTPException(status_code=401, detail="Expired code")
    except cognito.exceptions.LimitExceededException:
        raise HTTPException(status_code=429, detail="Too many requests")
    except cognito.exceptions.NotAuthorizedException:
        return {"message": "Email already confirmed"}
    return {"message": "Confirmed"}


@router.public.post("/cognito-refresh-token")
async def cognito_token_refresh(
    cognito_refresh_token: str = Body(..., min_length=1, embed=True)
):
    """
    - 갱신 토큰으로 새로운 인증 토큰을 발급
    - 갱신 토큰은 POST /api/auth/user 엔드포인트로 발급받을 수 있음
    - Response: 인증 토큰
    """
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


@router.public.post("/is-reregistration")
async def check_is_reregistration(
    email: str = Body(..., min_length=1),
    phone: str = Body(..., min_length=1),
):
    """
    - 이메일과 전화번호를 통해 회원가입 내역이 있는지 확인
    - Response: 중복 회원가입 여부
    """
    return {"reregistration": await db.signup_history_exists(email, phone)}
