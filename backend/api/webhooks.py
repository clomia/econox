from fastapi import Request

from backend.http import APIRouter

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
    payload["event_type"]
    return {}
