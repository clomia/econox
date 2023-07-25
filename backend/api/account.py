import base64
from uuid import uuid4
from pprint import pprint

import jwt
import boto3
import requests
from jwcrypto import jwk
from pydantic import BaseModel
from fastapi import Request, HTTPException, Depends

from backend.api import router
from backend.system import SECRETS

region = "us-east-1"
cognito = boto3.client("cognito-idp", region_name=region)

jwks_url = f"https://cognito-idp.{region}.amazonaws.com/{SECRETS['COGNITO_USER_POOL_ID']}/.well-known/jwks.json"
jwks = requests.get(jwks_url).json()


def base64_encode(value: str) -> str:
    """utf-8 -> ascii"""  # 안쓰지만 명시만 해놓은 함수
    return base64.b64encode(value.encode("utf-8")).decode("utf-8")


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


class PaymentData(BaseModel):
    amount: float
    productName: str
    customerEmail: str
    customerName: str


@router.post("/account")
def signup(item: Signup):
    print(f"요청 수신! {item}")
    response = cognito.sign_up(
        ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
        Username=item.email,
        Password=item.password,
        UserAttributes=[
            {"Name": "email", "Value": item.email},
        ],
    )
    print(response)
    return {}


@router.post("/account/email-verifi")
def email_verifi(item: VerifiCode):
    print(f"요청 수신! {item}")
    response = cognito.confirm_sign_up(
        ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
        Username=item.email,
        ConfirmationCode=item.code,
    )
    print(response)
    return {}


@router.post("/login")
def login(item: Login):
    response = cognito.admin_initiate_auth(
        UserPoolId=SECRETS["COGNITO_USER_POOL_ID"],
        ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
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
    print(jwks)
    jwk_key_dict = next((key for key in jwks["keys"] if key["kid"] == kid), None)
    if not jwk_key_dict:
        raise HTTPException(status_code=401, detail="Public key not found in jwks")

    # 4. JWK를 PEM 형식으로 변환
    key = jwk.JWK(**jwk_key_dict)
    pem_key = key.export_to_pem()

    # 5. 토큰 디코드
    app_client_id = SECRETS["COGNITO_APP_CLIENT_ID"]
    claims = jwt.decode(id_token, pem_key, algorithms=["RS256"], audience=app_client_id)
    # 6. JWT Claims 검증
    iss = (
        f"https://cognito-idp.{region}.amazonaws.com/{SECRETS['COGNITO_USER_POOL_ID']}"
    )
    if claims["iss"] != iss:
        raise HTTPException(status_code=401, detail="Invalid token issuer")
    if "aud" in claims and claims["aud"] != app_client_id:
        raise HTTPException(status_code=401, detail="Invalid audience claim")
    if claims["token_use"] != "id":
        raise HTTPException(status_code=401, detail="Invalid token use claim")

    return {"email": claims["email"]}


@router.post("/token-test")
def test_func(user_info=Depends(token_auth)):
    print("test func", user_info)
    return {"message": "Token is valid!"}


@router.post("/user-info")
def user_info(item: TextInput, info=Depends(token_auth)):
    print(item.text)
    print(info)
    return info


@router.post("/token-refresh")
def token_refresh(request: Request):
    ref_token = request.headers.get("refreshToken")
    response = cognito.initiate_auth(
        AuthFlow="REFRESH_TOKEN_AUTH",
        AuthParameters={"REFRESH_TOKEN": ref_token},
        ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
    )
    id_token = response["AuthenticationResult"]["IdToken"]
    return {"idToken": id_token}


@router.post("/payment")
def payment(item: PaymentData, info=Depends(token_auth)):
    print(item)
    toss_url = "https://api.tosspayments.com/v1/billing/authorizations/card"
    API_KEY = "test_sk_Wd46qopOB89RxLv54n73ZmM75y0v:"

    headers = {
        "Authorization": f"Basic {base64_encode(API_KEY)}",
        "Content-Type": "application/json",
        "Accept-Language": "en-US",
    }
    customerKey = uuid4().hex
    payload = {
        "customerKey": customerKey,
        "cardNumber": 1234123424301234,
        "cardExpirationYear": "12",
        "cardExpirationMonth": "12",
        "customerIdentityNumber": "121212",
    }

    response = requests.post(toss_url, headers=headers, json=payload)
    print(response.json())
    return response.json()


@router.post("/real-billing")
async def payment(request: Request, info=Depends(token_auth)):
    data = await request.json()
    billing_key = data["billingKey"]
    customer_key = data["customerKey"]
    toss_url = f"https://api.tosspayments.com/v1/billing/{billing_key}"
    API_KEY = "test_sk_Wd46qopOB89RxLv54n73ZmM75y0v:"

    headers = {
        "Authorization": f"Basic {base64_encode(API_KEY)}",
        "Content-Type": "application/json",
        "Accept-Language": "en-US",
    }
    payload = {
        "customerKey": customer_key,
        "amount": 4900,
        "orderId": uuid4().hex,
        "orderName": "토스 프라임 구구독독",
        "customerEmail": "clomia.sig@gmail.com",
    }

    response = requests.post(toss_url, headers=headers, json=payload)
    print(response.json())
    return response.json()
