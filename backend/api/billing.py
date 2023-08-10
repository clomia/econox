import base64
from uuid import uuid4

import requests
from fastapi import Body, HTTPException
from pydantic import BaseModel

from backend.api import router
from backend.system import SECRETS

API_PREFIX = "billing"


class CreditCard(BaseModel):
    user_id: str
    card_number: str
    expiration_year: str
    expiration_month: str
    owner_id: str


@router.post("/billing/tosspayments", tags=[API_PREFIX])
async def login(item: CreditCard):
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
    response = requests.post(
        tosspayments_host + "/v1/billing/authorizations/card",
        headers=headers,
        json=payload,
    )
    if response.status_code != 200:
        raise HTTPException(status_code=400)
    return {"billing_key": response.json()["billingKey"]}
