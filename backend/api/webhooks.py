from fastapi import Request, Depends

from backend import db
from backend.http import APIRouter, PayPalAPI

router = APIRouter("webhooks")


@router.public.post("/paypal", dependencies=[Depends(PayPalAPI.verify_webhook)])
async def paypal_webhook_handler(request: Request):
    payload = await request.json()

    print(request)
    print(request.headers)
    print(payload)
    return {}
