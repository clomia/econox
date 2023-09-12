from backend.http import APIRouter
from backend.system import SECRETS, membership

router = APIRouter("const")


@router.public.get("/paypal")
async def paypal_info():
    return {
        "client_id": SECRETS["PAYPAL_CLIENT_ID"],
        "plan_id": {
            "basic": membership["basic"]["paypal_plan"],
            "professional": membership["professional"]["paypal_plan"],
        },
    }
