from backend.http import APIRouter
from backend.system import SECRETS, MEMBERSHIP

router = APIRouter("const")


@router.public.get("/paypal")
async def paypal_info():
    return {
        "client_id": SECRETS["PAYPAL_CLIENT_ID"],
        "plan_id": {
            "basic": MEMBERSHIP["basic"]["paypal_plan"],
            "professional": MEMBERSHIP["professional"]["paypal_plan"],
        },
    }
