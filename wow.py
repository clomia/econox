from datetime import datetime
import asyncio
import pytz


def paypaltime2datetime(timestring: str) -> datetime:
    """PayPal에서 사용하는 시간 문자열을 한국 시간대로 변환한 datetime 객체로 만들어 반환합니다."""
    return (
        datetime.fromisoformat(timestring.replace("Z", "+00:00"))
        .astimezone(pytz.utc)
        .astimezone(pytz.timezone("Asia/Seoul"))
    )


def datetime2paypaltime(dt: datetime) -> str:
    """datetime 객체를 PayPal에서 사용하는 시간 문자열로 변환합니다. (ISO 8601)"""
    return dt.strftime("%Y-%m-%dT%H:%M:%S.%f") + "+09:00"


from backend.http import PayPalAPI


order_id = "9N400596SG422161B"


async def func():
    r = await PayPalAPI(
        f"/v1/notifications/webhooks-events/WH-0L227028K37382017-4T294655LV409563L"
    ).get()
    print(r)


asyncio.run(func())
{
    "status": "ACTIVE",
    "status_update_time": "2023-09-20T04:11:23Z",
    "id": "I-G7ALBP85F9JY",
    "plan_id": "P-32P35738U4826650TMT72TNA",
    "start_time": "2023-09-20T04:09:41Z",
    "quantity": "1",
    "shipping_amount": {"currency_code": "USD", "value": "0.0"},
    "subscriber": {
        "email_address": "testuser123@email.com",
        "payer_id": "5X8E6KMDML6RA",
        "name": {"given_name": "John", "surname": "Doe"},
        "shipping_address": {
            "address": {
                "address_line_1": "123 Elm Street",
                "address_line_2": "Apt #4B",
                "admin_area_2": "Springfield",
                "admin_area_1": "IL",
                "postal_code": "62701",
                "country_code": "US",
            }
        },
    },
    "billing_info": {
        "outstanding_balance": {"currency_code": "USD", "value": "0.0"},
        "cycle_executions": [
            {
                "tenure_type": "REGULAR",
                "sequence": 1,
                "cycles_completed": 1,
                "cycles_remaining": 0,
                "current_pricing_scheme_version": 1,
                "total_cycles": 0,
            }
        ],
        "last_payment": {
            "amount": {"currency_code": "USD", "value": "9.99"},
            "time": "2023-09-20T04:11:23Z",
        },
        "next_billing_time": "2023-10-20T10:00:00Z",
        "failed_payments_count": 0,
    },
    "create_time": "2023-09-20T04:11:22Z",
    "update_time": "2023-09-20T04:11:23Z",
    "plan_overridden": False,
    "links": [
        {
            "href": "https://api.sandbox.paypal.com/v1/billing/subscriptions/I-G7ALBP85F9JY/cancel",
            "rel": "cancel",
            "method": "POST",
        },
        {
            "href": "https://api.sandbox.paypal.com/v1/billing/subscriptions/I-G7ALBP85F9JY",
            "rel": "edit",
            "method": "PATCH",
        },
        {
            "href": "https://api.sandbox.paypal.com/v1/billing/subscriptions/I-G7ALBP85F9JY",
            "rel": "self",
            "method": "GET",
        },
        {
            "href": "https://api.sandbox.paypal.com/v1/billing/subscriptions/I-G7ALBP85F9JY/suspend",
            "rel": "suspend",
            "method": "POST",
        },
        {
            "href": "https://api.sandbox.paypal.com/v1/billing/subscriptions/I-G7ALBP85F9JY/capture",
            "rel": "capture",
            "method": "POST",
        },
    ],
}
