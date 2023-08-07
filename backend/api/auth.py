""" user & auth """
from typing import Dict

import jwt
import boto3
import requests
from pydantic import BaseModel
from fastapi import HTTPException
from fastapi.responses import Response

from backend.api import router
from backend.system import SECRETS

API_PREFIX = "auth"

region = "us-east-1"
cognito = boto3.client("cognito-idp", region_name=region)
jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{SECRETS['COGNITO_USER_POOL_ID']}/.well-known/jwks.json"
jwks = requests.get(jwks_url).json()


class UserAuth(BaseModel):
    email: str
    password: str


@router.post("/auth/user", tags=[API_PREFIX])
async def login(item: UserAuth):
    # todo 올싸인아웃 후 로그인해서 다른 세션 종료시키기
    # todo DB에 해당 유저의 레코드가 없으면 회원가입 완료 안된거니까 401 쏴주기
    try:
        result = cognito.initiate_auth(
            ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": item.email, "PASSWORD": item.password},
        )
    except cognito.exceptions.NotAuthorizedException:
        raise HTTPException(status_code=401)
    return {
        "id_token": result["AuthenticationResult"]["IdToken"],
        "refresh_token": result["AuthenticationResult"]["RefreshToken"],
    }


class EmailAuth(BaseModel):
    email: str
    verification_code: str


@router.post("/auth/email", tags=[API_PREFIX])
async def signup_email_verification(item: EmailAuth):
    try:
        cognito.confirm_sign_up(
            ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
            Username=item.email,
            ConfirmationCode=item.verification_code,
        )
    except cognito.exceptions.CodeMismatchException:
        raise HTTPException(status_code=409)
    except cognito.exceptions.ExpiredCodeException:
        raise HTTPException(status_code=401)
    return Response(status_code=200)


class RefreshToken(BaseModel):
    refresh_token: str


@router.post("/auth/refresh-token", tags=[API_PREFIX])
async def token_refresh(item: RefreshToken) -> Dict[str, str]:
    try:
        result = cognito.initiate_auth(
            AuthFlow="REFRESH_TOKEN_AUTH",
            AuthParameters={"REFRESH_TOKEN": item.refresh_token},
            ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
        )
    except cognito.exceptions.NotAuthorizedException:
        raise HTTPException(status_code=401)
    return {"id_token": result["AuthenticationResult"]["IdToken"]}
