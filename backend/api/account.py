import jwt
import boto3
import requests
from pydantic import BaseModel
from fastapi import HTTPException

from backend.api import router
from backend.system import SECRETS

region = "us-east-1"
cognito = boto3.client("cognito-idp", region_name=region)
jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{SECRETS['COGNITO_USER_POOL_ID']}/.well-known/jwks.json"
jwks = requests.get(jwks_url).json()


class LoginInput(BaseModel):
    email: str
    password: str


class SignupInput(LoginInput):
    password2: str


@router.post("/auth/user")
async def login(item: LoginInput):
    try:
        response = cognito.initiate_auth(
            ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
            AuthFlow="USER_PASSWORD_AUTH",
            AuthParameters={"USERNAME": item.email, "PASSWORD": item.password},
        )
    except cognito.exceptions.NotAuthorizedException:
        raise HTTPException(status_code=401)
    return {
        "idToken": response["AuthenticationResult"]["IdToken"],
        "refreshToken": response["AuthenticationResult"]["RefreshToken"],
    }
