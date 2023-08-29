import base64

import httpx
from fastapi import HTTPException
from pydantic import BaseModel

from backend.http import Router
from backend.system import SECRETS

router = Router("billing")


class CreditCard(BaseModel):
    user_id: str
    card_number: str
    expiration_year: str
    expiration_month: str
    owner_id: str


@router.public.post("/billing/tosspayments")
async def create_tosspayments_billing_key(item: CreditCard):
    tosspayments_host = "https://api.tosspayments.com"

    basic = SECRETS["TOSSPAYMENTS_SECRET_KEY"] + ":"
    token = base64.b64encode(basic.encode("utf-8")).decode("utf-8")

    headers = {
        "Authorization": f"Basic {token}",
        "Content-Type": "application/json",
    }
    payload = {
        "customerKey": item.user_id,
        "cardNumber": item.card_number,
        "cardExpirationYear": item.expiration_year,
        "cardExpirationMonth": item.expiration_month,
        "customerIdentityNumber": item.owner_id,
    }
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            tosspayments_host + "/v1/billing/authorizations/card",
            headers=headers,
            json=payload,
        )
    if resp.status_code != 200:  # Tosspayments가 정의한 에러 양식을 그대로 사용합니다. 아래 URL을 참조하세요
        # https://docs.tosspayments.com/reference/error-codes#카드-자동결제-빌링키-발급-요청
        raise HTTPException(resp.status_code, detail=resp.json()["code"])
    return {"tosspayments_billing_key": resp.json()["billingKey"]}
