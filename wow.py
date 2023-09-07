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

headers = {
    "Content-Type": "application/json",
    "Authorization": "Bearer ECvJ_yBNz_UfMmCvWEbT_2ZWXdzbFFQZ-1Y5K2NGgeHn",
}

data = {
    "transmission_id": "69cd13f0-d67a-11e5-baa3-778b53f4ae55",
    "transmission_time": "2016-02-18T20:01:35Z",
    "cert_url": "cert_url",
    "auth_algo": "SHA256withRSA",
    "transmission_sig": "lmI95Jx3Y9nhR5SJWlHVIWpg4AgFk7n9bCHSRxbrd8A9zrhdu2rMyFrmz Zjh3s3boXB07VXCXUZy/UFzUlnGJn0wDugt7FlSvdKeIJenLRemUxYCPVoEZzg9VFNqOa48gMkvF XTpxBeUx/kWy6B5cp7GkT2 pOowfRK7OaynuxUoKW3JcMWw272VKjLTtTAShncla7tGF 55rxyt2KNZIIqxNMJ48RDZheGU5w1npu9dZHnPgTXB9iomeVRoD8O/jhRpnKsGrDschyNdkeh81BJJMH4Ctc6lnCCquoP/GzCzz33MMsNdid7vL/NIWaCsekQpW26FpWPi/tfj8nLA': '=",
    "webhook_id": "1JE4291016473214C",
    "webhook_event": {
        "id": "8PT597110X687430LKGECATA",
        "create_time": "2013-06-25T21:41:28Z",
        "resource_type": "authorization",
        "event_type": "PAYMENT.AUTHORIZATION.CREATED",
        "summary": "A payment authorization was created",
        "resource": {
            "id": "2DC87612EK520411B",
            "create_time": "2013-06-25T21:39:15Z",
            "update_time": "2013-06-25T21:39:17Z",
            "state": "authorized",
            "amount": {
                "total": "7.47",
                "currency": "USD",
                "details": {"subtotal": "7.47"},
            },
            "parent_payment": "PAY-36246664YD343335CKHFA4AY",
            "valid_until": "2013-07-24T21:39:15Z",
            "links": [
                {
                    "href": "https://api-m.paypal.com/v1/payments/authorization/2DC87612EK520411B",
                    "rel": "self",
                    "method": "GET",
                },
                {
                    "href": "https://api-m.paypal.com/v1/payments/authorization/2DC87612EK520411B/capture",
                    "rel": "capture",
                    "method": "POST",
                },
                {
                    "href": "https://api-m.paypal.com/v1/payments/authorization/2DC87612EK520411B/void",
                    "rel": "void",
                    "method": "POST",
                },
                {
                    "href": "https://api-m.paypal.com/v1/payments/payment/PAY-36246664YD343335CKHFA4AY",
                    "rel": "parent_payment",
                    "method": "GET",
                },
            ],
        },
    },
}

response = requests.post(
    "https://api-m.sandbox.paypal.com/v1/notifications/verify-webhook-signature",
    headers=headers,
    json=data,
)
