import base64
import requests
from datetime import datetime

from pydantic import BaseModel
from fastapi import HTTPException
from fastapi.responses import Response

from backend.api import router
from backend.system import SECRETS

API_PREFIX = "billing"


class CardRegist(BaseModel):
    number: str
    expir_year: str
    expir_month: str
    identity: str
    user_id: str


@router.post("/billing/tosspayments/card", tags=[API_PREFIX])
async def tosspayments_card_registration(item: CardRegist):
    url = "https://api.tosspayments.com/v1/billing/authorizations/card"
    basic = SECRETS["TOSSPAYMENTS_SECRET_KEY"] + ":"
    api_key = base64.b64encode(basic.encode("utf-8")).decode("utf-8")
    headers = {
        "Authorization": f"Basic {api_key}",
        "Content-Type": "application/json",
    }
    payload = {
        "customerKey": item.user_id,
        "cardNumber": item.number,
        "cardExpirationYear": item.expir_year,
        "cardExpirationMonth": item.expir_month,
        "customerIdentityNumber": item.identity,
    }
    result = requests.post(url, headers=headers, json=payload).json()
    result["billingKey"]
    result["cardNumber"]
    result["cardCompany"]

    return Response(status_code=200)
