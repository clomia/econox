from pydantic import BaseModel, constr

from backend.http import Router, TosspaymentsAPI

router = Router("billing")


class CreditCard(BaseModel):
    user_id: constr(min_length=1)
    card_number: constr(min_length=1)
    expiration_year: constr(min_length=1)
    expiration_month: constr(min_length=1)
    owner_id: constr(min_length=1)


@router.public.post("/billing/tosspayments")
async def create_tosspayments_billing_key(item: CreditCard):
    resp = await TosspaymentsAPI("/v1/billing/authorizations/card").post(
        {
            "customerKey": item.user_id,
            "cardNumber": item.card_number,
            "cardExpirationYear": item.expiration_year,
            "cardExpirationMonth": item.expiration_month,
            "customerIdentityNumber": item.owner_id,
        }
    )
    return {"key": resp["billingKey"]}
