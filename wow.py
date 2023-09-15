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

subscription_id = "I-KGJTYVN9N7UL"

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
        "plan": {
            "payment_preferences": {"setup_fee": {"currency_code": "USD", "value": 1.3}}
        },
    },
)

# Extract approval link from response
print(response.json())
# url = next(ele["href"] for ele in response.json()["links"] if ele["rel"] == "approve")
# print(f"Approve link: {url}")

# response = requests.post(
#     f"https://api.sandbox.paypal.com/v1/billing/subscriptions/{subscription_id}/suspend",
#     headers={
#         "Authorization": f"Bearer {access_token}",
#         "Content-Type": "application/json",
#     },
#     json={"reason": "Tuaest"},
# )

# response = requests.post(
#     f"https://api.sandbox.paypal.com/v1/billing/subscriptions/{subscription_id}/activate",
#     headers={
#         "Authorization": f"Bearer {access_token}",
#         "Content-Type": "application/json",
#     },
# )


# url = f"https://api.sandbox.paypal.com/v1/billing/subscriptions/{subscription_id}"

# headers = {
#     "Authorization": f"Bearer {access_token}",
#     "Content-Type": "application/json",
# }

# # `start_time` 수정 payload
# data = [{"op": "replace", "path": "/start_time", "value": "2023-09-23T00:00:00Z"}]

# response = requests.patch(url, headers=headers, json=data)
# result = response.json()

# print(result)
