{
    "id": "WH-5P841626K1319501S-93T49540D8390830S",
    "event_version": "1.0",
    "create_time": "2023-10-26T11:11:00.892Z",
    "resource_type": "sale",
    "event_type": "PAYMENT.SALE.COMPLETED",
    "summary": "Payment completed for $ 9.99 USD",
    "resource": {
        "billing_agreement_id": "I-CP18AJLYDWR2",
        "amount": {"total": "9.99", "currency": "USD", "details": {"subtotal": "9.99"}},
        "payment_mode": "INSTANT_TRANSFER",
        "update_time": "2023-10-26T11:10:43Z",
        "create_time": "2023-10-26T11:10:43Z",
        "protection_eligibility_type": "ITEM_NOT_RECEIVED_ELIGIBLE,UNAUTHORIZED_PAYMENT_ELIGIBLE",
        "transaction_fee": {"currency": "USD", "value": "0.69"},
        "protection_eligibility": "ELIGIBLE",
        "links": [
            {
                "method": "GET",
                "rel": "self",
                "href": "https://api.sandbox.paypal.com/v1/payments/sale/7WT2824826029771W",
            },
            {
                "method": "POST",
                "rel": "refund",
                "href": "https://api.sandbox.paypal.com/v1/payments/sale/7WT2824826029771W/refund",
            },
        ],
        "id": "7WT2824826029771W",
        "state": "completed",
        "invoice_number": "",
    },
    "links": [
        {
            "href": "https://api.sandbox.paypal.com/v1/notifications/webhooks-events/WH-5P841626K1319501S-93T49540D8390830S",
            "rel": "self",
            "method": "GET",
        },
        {
            "href": "https://api.sandbox.paypal.com/v1/notifications/webhooks-events/WH-5P841626K1319501S-93T49540D8390830S/resend",
            "rel": "resend",
            "method": "POST",
        },
    ],
}
