import json
from pprint import pprint

import jwt
import boto3
import requests
from jwcrypto import jwk
from pydantic import BaseModel
from fastapi import Request, HTTPException, Depends

from backend.api import router
from backend.system import COGNITO_USER_POOL

region = "us-east-1"
cognito = boto3.client("cognito-idp", region_name=region)

jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{COGNITO_USER_POOL}/.well-known/jwks.json"
jwks = requests.get(jwks_url).json()


class Signup(BaseModel):
    email: str
    password: str


class Login(BaseModel):
    email: str
    password: str


class VerifiCode(BaseModel):
    email: str
    code: str


class TextInput(BaseModel):
    text: str


@router.post("/account")
def signup(item: Signup):
    print(f"요청 수신! {item}")
    response = cognito.sign_up(
        ClientId="35v965qnmbsjhdh0i6gfjg3rjs",
        Username=item.email,
        Password=item.password,
        UserAttributes=[
            {"Name": "email", "Value": item.email},
            {"Name": "name", "Value": "샘플 이름"},
            {"Name": "custom:membership_type", "Value": "basic"},
            {"Name": "custom:membership_expire", "Value": "2023-09-13"},
        ],
    )
    print(response)
    return {}


@router.post("/account/email-verifi")
def email_verifi(item: VerifiCode):
    print(f"요청 수신! {item}")
    response = cognito.confirm_sign_up(
        ClientId="35v965qnmbsjhdh0i6gfjg3rjs",
        Username=item.email,
        ConfirmationCode=item.code,
    )
    print(response)
    return {}


@router.post("/login")
def login(item: Login):
    response = cognito.admin_initiate_auth(
        UserPoolId="us-east-1_4FfzJH2Zw",
        ClientId="35v965qnmbsjhdh0i6gfjg3rjs",
        AuthFlow="ADMIN_USER_PASSWORD_AUTH",
        AuthParameters={"USERNAME": item.email, "PASSWORD": item.password},
    )
    # Access Token 복호화
    decoded_access_token = jwt.decode(
        response["AuthenticationResult"]["AccessToken"],
        options={"verify_signature": False},
    )
    print("----Decoded Access Token ----")
    pprint(decoded_access_token)

    # ID Token 복호화
    decoded_id_token = jwt.decode(
        response["AuthenticationResult"]["IdToken"], options={"verify_signature": False}
    )
    print("----Decoded ID Token ----")
    pprint(decoded_id_token)

    # JWT 토큰 반환
    return {
        "accessToken": response["AuthenticationResult"]["AccessToken"],
        "idToken": response["AuthenticationResult"]["IdToken"],
        "refreshToken": response["AuthenticationResult"]["RefreshToken"],
    }


def token_auth(request: Request):
    print(request)
    # 1. 요청 헤더에서 토큰 가져오기
    id_token = request.headers.get("idtoken")
    if not id_token:
        raise HTTPException(status_code=400, detail="idtoken header not found")

    # 3. 토큰 헤더에서 kid 가져오기
    try:
        headers = jwt.get_unverified_header(id_token)
    except:
        raise HTTPException(status_code=401, detail="토큰 디코딩 에러")
    kid = headers["kid"]
    jwk_key_dict = next((key for key in jwks["keys"] if key["kid"] == kid), None)
    if not jwk_key_dict:
        raise HTTPException(status_code=401, detail="Public key not found in jwks")

    # 4. JWK를 PEM 형식으로 변환
    key = jwk.JWK(**jwk_key_dict)
    pem_key = key.export_to_pem()

    # 5. 토큰 디코드
    app_client_id = "35v965qnmbsjhdh0i6gfjg3rjs"
    claims = jwt.decode(id_token, pem_key, algorithms=["RS256"], audience=app_client_id)
    print(claims)
    # 6. JWT Claims 검증
    iss = f"https://cognito-idp.{region}.amazonaws.com/{COGNITO_USER_POOL}"
    if claims["iss"] != iss:
        raise HTTPException(status_code=401, detail="Invalid token issuer")
    if "aud" in claims and claims["aud"] != app_client_id:
        raise HTTPException(status_code=401, detail="Invalid audience claim")
    if claims["token_use"] != "id":
        raise HTTPException(status_code=401, detail="Invalid token use claim")

    return {
        "email": claims["email"],
        "name": claims["name"],
        "membership": {
            "type": claims["custom:membership_type"],
            "expire": claims["custom:membership_expire"],
        },
    }


@router.post("/token-test")
def test_func(user_info=Depends(token_auth)):
    print("test func", user_info)
    return {"message": "Token is valid!"}


@router.post("/user-info")
def user_info(item: TextInput, info=Depends(token_auth)):
    print(item.text)
    print(info)
    return info
