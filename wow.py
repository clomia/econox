import requests
import base64

from datetime import datetime, timezone, timedelta

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

KST = timezone(timedelta(hours=9))  # 타임존이 포함된 isoformat 문자열 생성에 필요
now = datetime.now(KST)

params = {
    "start_time": (now - timedelta(days=365)).isoformat(),
    "end_time": now.isoformat(),
}
print(params)
response = requests.get(
    f"https://api.sandbox.paypal.com/v1/billing/subscriptions/{subscription_id}/transactions",
    headers={
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    },
    params=params,
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

{
    "status": "COMPLETED",
    "id": "80T226218J797090S",
    "amount_with_breakdown": {
        "gross_amount": {"currency_code": "USD", "value": "12.99"},
        "fee_amount": {"currency_code": "USD", "value": "0.81"},
        "net_amount": {"currency_code": "USD", "value": "12.18"},
    },
    "payer_name": {"given_name": "John", "surname": "Doe"},
    "payer_email": "sb-sfvgh27139304@personal.example.com",
    "time": "2023-09-14T07:02:18.000Z",
}
