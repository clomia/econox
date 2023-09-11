import sys
import base64
from pathlib import Path

import requests

parent_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(parent_dir))

from backend.system import SECRETS

is_prod = input("프로덕션 환경인 경우 (Y)를 입력해주세요 / 샌드박스 환경인 경우 (Enter)를 누르세요: ") == "Y"
host = "https://api.paypal.com" if is_prod else "https://api.sandbox.paypal.com"

try:
    token = base64.b64encode(
        f"{SECRETS['PAYPAL_CLIENT_ID']}:{SECRETS['PAYPAL_SECRET_KEY']}".encode("utf-8")
    ).decode("utf-8")
    response = requests.post(
        f"{host}/v1/oauth2/token",
        headers={
            "Authorization": f"basic {token}",
            "Content-Type": "application/x-www-form-urlencoded",
        },
        data={"grant_type": "client_credentials"},
    )
    token_info = response.json()
    access_token = token_info["access_token"]
except Exception as e:
    print("토큰 발급에 실패하였습니다. SECRET값 PAYPAL_CLIENT_ID과 PAYPAL_SECRET_KEY가 올바른지 확인해주세요")
    raise e

headers = {
    "Authorization": f"Bearer {access_token}",
    "Content-Type": "application/json",
}

resp = requests.post(
    f"{host}/v1/catalogs/products",
    headers=headers,
    json={
        "name": "Econox Membership",
        "type": "SERVICE",
        "category": "SOFTWARE",
        "home_url": "https://www.econox.io",
    },
).json()

print(f"\n요청 완료, 응답: {resp}")

print(
    f"""
Product가 성공적으로 생성되었습니다.

Econox Membership - Product ID: {resp["id"]}
"""
)
