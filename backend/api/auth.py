import secrets

import jwt
import boto3
import requests
from fastapi import Body, HTTPException
from fastapi.responses import Response

from backend.api import router
from backend.system import SECRETS, EFS_VOLUME_PATH

API_PREFIX = "auth"
PHONE_CONFIRMATION_CACHE_PATH = EFS_VOLUME_PATH / "phone_confirmation_cache"
PHONE_CONFIRMATION_CACHE_PATH.mkdir(parents=True, exist_ok=True)


region = "us-east-1"
cognito = boto3.client("cognito-idp", region_name=region)
jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{SECRETS['COGNITO_USER_POOL_ID']}/.well-known/jwks.json"
jwks = requests.get(jwks_url).json()


@router.post("/auth/user", tags=[API_PREFIX])
async def login(email: str = Body(...), password: str = Body(...)):
    # 올싸인아웃 후 로그인해서 다른 세션 종료시키기
    # DB에 해당 유저의 레코드가 없으면 회원가입 완료 안된거니까 401 쏴주기
    try:
        result = cognito.initiate_auth(
            ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": email, "PASSWORD": password},
        )
    except cognito.exceptions.NotAuthorizedException:
        raise HTTPException(status_code=401)
    return {
        "id_token": result["AuthenticationResult"]["IdToken"],
        "refresh_token": result["AuthenticationResult"]["RefreshToken"],
    }


@router.post("/auth/refresh-token", tags=[API_PREFIX])
async def token_refresh(refresh_token: str = Body(...)):
    try:
        result = cognito.initiate_auth(
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={"REFRESH_TOKEN": refresh_token},
            ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
        )
    except cognito.exceptions.NotAuthorizedException:
        raise HTTPException(status_code=401)
    return {"id_token": result["AuthenticationResult"]["IdToken"]}


# 로그인된 유저가 요청 헤더에 담는 토큰을 보고 검사 & 누구인지 확인하는 라우터 전처리 함수(인터셉터) 만들어야 함


@router.post("/auth/phone", tags=[API_PREFIX])
async def create_phone_confirmation(phone_number: str = Body(...)):
    # +82하고 010 으로 시작해야 함
    target_path = PHONE_CONFIRMATION_CACHE_PATH / phone_number
    issued_code = f"{secrets.randbelow(10**6):06}"
    target_path.write_text(issued_code)
    try:
        sns = boto3.client("sns", region_name=region)
        message = f"ECONOX confirmation code: {issued_code}"
        response = sns.publish(PhoneNumber=phone_number, Message=message)
    except Exception as e:  # 에러 경우가 너무 많으므로 퉁쳐서 500으로 처리
        target_path.unlink()
        raise e
    return Response(status_code=200)


@router.post("/auth/phone/confirm", tags=[API_PREFIX])
async def phone_confirmation(
    phone_number: str = Body(...), confirmation_code: str = Body(...)
):
    target_path = PHONE_CONFIRMATION_CACHE_PATH / phone_number
    try:
        issued_code = target_path.read_text()
        if issued_code == confirmation_code:
            return Response(status_code=200)
        else:
            return HTTPException(status_code=401)
    finally:
        target_path.unlink(missing_ok=True)


@router.post("/auth/email/confirm", tags=[API_PREFIX])
async def cognito_email_confirmation(
    email: str = Body(...), confirmation_code: str = Body(...)
):
    try:
        cognito.confirm_sign_up(
            ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
            Username=email,
            ConfirmationCode=confirmation_code,
        )
    except cognito.exceptions.CodeMismatchException:
        raise HTTPException(status_code=409)
    except cognito.exceptions.ExpiredCodeException:
        raise HTTPException(status_code=401)
    return Response(status_code=200)
