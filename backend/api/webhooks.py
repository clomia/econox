from fastapi import Request, Depends

from backend.http import APIRouter, PayPalAPI
from backend.system import SECRETS

router = APIRouter("webhooks")


@router.public.post("/paypal", dependencies=[Depends(PayPalAPI.verify_webhook)])
async def paypal_webhook(request: Request):
    """
    - 으앙
    - Response: BillingKey
    """
    payload = await request.json()
    print(request)
    print(request.headers)
    print(payload)
    return {}
