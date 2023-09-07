from fastapi import Request

from backend.http import APIRouter, PayPalAPI
from backend.system import SECRETS

router = APIRouter("webhooks")


@router.public.post("/paypal")
async def paypal_webhook(request: Request):
    """
    - 으앙
    - Response: BillingKey
    """
    payload = await request.json()
    print(request)
    print(request.headers)
    print(payload)
    await PayPalAPI("/v1/notifications/verify-webhook-signature").post(
        {
            "auth_algo": request.headers["paypal-auth-algo"],
            "cert_url": request.headers["paypal-cert-url"],
            "transmission_id": request.headers["paypal-transmission-id"],
            "transmission_sig": request.headers["paypal-transmission-sig"],
            "transmission_time": request.headers["paypal-transmission-time"],
            "webhook_id": SECRETS["PAYPAL_WEBHOOK_ID"],
            "webhook_event": payload,
        }
    )
    return {}
