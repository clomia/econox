from datetime import datetime
from backend.math import next_billing_date, next_billing_date_adjust_membership_change

# Origin Next: 2022-12-31 00:00:00
base = datetime(2023, 1, 8)  # base = datetime(2022, 10, 31)
current = datetime(2022, 11, 30)

next_billing = next_billing_date(base=base, current=current)

adjust_next_billing = next_billing_date_adjust_membership_change(
    base_billing=base,
    current_billing=current,
    current_membership="professional",
    new_membership="basic",
    change_day=datetime(2022, 12, 3),
    currency="USD",
)


print(f"Origin Next: {next_billing}\nAdjust Next: {adjust_next_billing}")
