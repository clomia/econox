import requests
import base64

from backend.system import SECRETS

# 1. OAuth2 토큰 가져오기
token = base64.b64encode(
    f"{SECRETS['PAYPAL_CLIENT_ID']}:{SECRETS['PAYPAL_SECRET_KEY']}".encode("utf-8")
).decode("utf-8")
response = requests.post(
    "https://api.sandbox.paypal.com/v1/oauth2/token",
    headers={
        "Authorization": f"basic {token}",
        "Content-Type": "application/x-www-form-urlencoded",
    },
    data={"grant_type": "client_credentials"},
)
token_info = response.json()
access_token = token_info["access_token"]

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
}


data = {
    "product_id": SECRETS["PAYPAL_PROD_ID"],
    "name": "For test",
    "billing_cycles": [
        {
            "tenure_type": "REGULAR",
            "sequence": 1,
            "total_cycles": 0,
            "pricing_scheme": {"fixed_price": {"currency_code": "USD", "value": "54"}},
            "frequency": {
                "interval_unit": "MONTH",
                "interval_count": 1,
            },
        }
    ],
    "payment_preferences": {"setup_fee": {"currency_code": "USD", "value": "12"}},
}

# response = requests.post(
#     f"https://api.sandbox.paypal.com/v1/billing/plans",
#     headers=headers,
#     json=data,
# )

# print(response.json())


subscription_id = "I-E0S6ARBB9CFA"

data = {
    "plan_id": "P-32V28517A81529932MT7MHJA",
}

# response = requests.post(
#     f"https://api.sandbox.paypal.com/v1/billing/subscriptions/{subscription_id}/revise",
#     headers=headers,
#     json=data,
# )

# print(response.json())

resp = requests.post(
    "https://api.sandbox.paypal.com/v1/billing/subscriptions/I-E0S6ARBB9CFA/capture",
    headers=headers,
    json={
        "note": "hello",
        "capture_type": "",
        "amount": {"currency_code": "USD", "value": "3.4"},
    },
)

print(resp.json())
