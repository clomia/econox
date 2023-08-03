import jwt
import boto3
import requests
from pydantic import BaseModel
from fastapi import HTTPException, Request
from fastapi.responses import Response

from backend.api import router
from backend.system import SECRETS

region = "us-east-1"
cognito = boto3.client("cognito-idp", region_name=region)
jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{SECRETS['COGNITO_USER_POOL_ID']}/.well-known/jwks.json"
jwks = requests.get(jwks_url).json()


class UserAuth(BaseModel):
    email: str
    password: str


@router.post("/auth/user", tags=["user"])
async def login(item: UserAuth):
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


@router.post("/user", tags=["user"])
async def signup(item: UserAuth):
    try:
        cognito.sign_up(
            ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
            Username=item.email,
            Password=item.password,
            UserAttributes=[
                {"Name": "email", "Value": item.email},
            ],
        )
    except cognito.exceptions.UsernameExistsException:
        raise HTTPException(status_code=409)
    return Response(status_code=200)


class EmailAuth(BaseModel):
    email: str
    confirmation_code: str


@router.post("/auth/email", tags=["auth"])
async def signup_email_verification(item: EmailAuth):
    try:
        cognito.confirm_sign_up(
            ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
            Username=item.email,
            ConfirmationCode=item.confirmation_code,
        )
        # 여기서 실제 앱 회원가입 로직을 돌려야 함! api 외부에 별도 함수로 만들어서 import
    except cognito.exceptions.CodeMismatchException:
        raise HTTPException(status_code=409)
    except cognito.exceptions.ExpiredCodeException:
        raise HTTPException(status_code=401)
    return Response(status_code=200)
