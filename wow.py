{
    "x-forwarded-for": "173.0.80.116",
    "x-forwarded-proto": "https",
    "x-forwarded-port": "443",
    "host": "www.econox.io",
    "x-amzn-trace-id": "Root=1-64f984c1-1021c9194459916a01c147cf",
    "content-length": "1228",
    "accept": "*/*",
    "paypal-transmission-id": "89556ce0-4d55-11ee-9f56-dd5f48f22b28",
    "paypal-transmission-time": "2023-09-07T08:07:06Z",
    "paypal-transmission-sig": "KZnM9kr70vxRNEBlNE0q4DRbNYasQOFEqQYxRatvWXx8ZVTr6taQmY9V+3SeOogL2pnqi+xB2S+N40Nsxy+nisl05+TwDPguU6BuAXoRsnaHPwDVEmqXlEQZIv2QP4WyZl7U4LH2SI9Q/T87uK1xKRDLqTqL9xx7SYPYb0+iXSBvbbiEvL4pSVWnGySOfj0gW08XByX8H0EeRaPLPhO2K2idL7LmGkkJMTQwzxla4P755qVWyOoJ1UfeDK+ThyjmXZsDIEL3vCsugASGKJ5VaRU+WmMMm7kWA1G4mVwNsxGiTBplUD4/VBXpdq0jDhmBfv9ga56rfZFoLfluNdNkGw==",
    "paypal-auth-version": "v2",
    "paypal-cert-url": "https://api.sandbox.paypal.com/v1/notifications/certs/CERT-360caa42-fca2a594-2d7ab011",
    "paypal-auth-algo": "SHA256withRSA",
    "content-type": "application/json",
    "user-agent": "PayPal/AUHD-214.0-58109767",
    "correlation-id": "f8426431e912e",
    "cal_poolstack": "amqunphttpdeliveryd:UNPHTTPDELIVERY*CalThreadId=0*TopLevelTxnStartTime=18a6eae9436*Host=ccg18amqunphttpdeliveryd11",
    "x-b3-spanid": "b608e1edc0dac8ef",
    "client_pid": "514263",
}
{
    "id": "WH-4BF08585W75823541-1TG34585CL883470E",
    "event_version": "1.0",
    "create_time": "2023-09-07T07:13:29.971Z",
    "resource_type": "sale",
    "event_type": "PAYMENT.SALE.COMPLETED",
    "summary": "Payment completed for $ 14.9 USD",
    "resource": {
        "billing_agreement_id": "I-0HNJGFKLTLMP",
        "amount": {
            "total": "14.90",
            "currency": "USD",
            "details": {"subtotal": "14.90"},
        },
        "payment_mode": "INSTANT_TRANSFER",
        "update_time": "2023-09-07T07:13:25Z",
        "create_time": "2023-09-07T07:13:25Z",
        "protection_eligibility_type": "ITEM_NOT_RECEIVED_ELIGIBLE,UNAUTHORIZED_PAYMENT_ELIGIBLE",
        "transaction_fee": {"currency": "USD", "value": "0.88"},
        "protection_eligibility": "ELIGIBLE",
        "links": [
            {
                "method": "GET",
                "rel": "self",
                "href": "https://api.sandbox.paypal.com/v1/payments/sale/5CS38179PL895402Y",
            },
            {
                "method": "POST",
                "rel": "refund",
                "href": "https://api.sandbox.paypal.com/v1/payments/sale/5CS38179PL895402Y/refund",
            },
        ],
        "id": "5CS38179PL895402Y",
        "state": "completed",
        "invoice_number": "",
    },
    "links": [
        {
            "href": "https://api.sandbox.paypal.com/v1/notifications/webhooks-events/WH-4BF08585W75823541-1TG34585CL883470E",
            "rel": "self",
            "method": "GET",
        },
        {
            "href": "https://api.sandbox.paypal.com/v1/notifications/webhooks-events/WH-4BF08585W75823541-1TG34585CL883470E/resend",
            "rel": "resend",
            "method": "POST",
        },
    ],
}
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

# 3. 결제 상세 정보 조회
url = f"https://api.sandbox.paypal.com/v1/payments/billing-agreements/I-9W96GNVTB5GV"
headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
}
sale_info = requests.get(url, headers=headers).json()
print(sale_info)
# 결제와 관련된 상세 정보 처리...
