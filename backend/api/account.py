import boto3
from pydantic import BaseModel

from backend.api import router

cognito = boto3.client("cognito-idp", region_name="us-east-1")


class Signup(BaseModel):
    email: str
    password: str


class VerifiCode(BaseModel):
    email: str
    code: str


@router.post("/account")
def signup(item: Signup):
    print(f"요청 수신! {item}")
    response = cognito.sign_up(
        ClientId="35v965qnmbsjhdh0i6gfjg3rjs",
        Username=item.email,
        Password=item.password,
        UserAttributes=[{"Name": "email", "Value": item.email}],
    )
    print(response)
    return {}


@router.post("/account/email-verifi")
def signup(item: VerifiCode):
    print(f"요청 수신! {item}")
    response = cognito.confirm_sign_up(
        ClientId="35v965qnmbsjhdh0i6gfjg3rjs",
        Username=item.email,
        ConfirmationCode=item.code,
    )
    print(response)
    return {}
