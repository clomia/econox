import requests
import base64

from backend.system import SECRETS, membership

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

access_token = ...
subscription_id = "I-96V62M5HRD3U"
plan_id = {
    "basic": "P-32P35738U4826650TMT72TNA",
    "professional": "P-8U118819R1222424SMT72UDI",
}

response = requests.post(
    f"https://api.sandbox.paypal.com/v1/billing/subscriptions/{subscription_id}/revise",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    },
    json={
        "plan_id": plan_id["basic"],
    },
)

# Extract approval link from response
url = next(ele["href"] for ele in response.json()["links"] if ele["rel"] == "approve")
print(f"Approve link: {url}")
