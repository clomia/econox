import boto3
import ipinfo
from fastapi import HTTPException, Request, Body

from backend.api import router
from backend.system import SECRETS, log

API_PREFIX = "user"

region = "us-east-1"
cognito = boto3.client("cognito-idp", region_name=region)


@router.post("/user/cognito", tags=[API_PREFIX])
async def create_cognito_user(email: str = Body(...), password: str = Body(...)):
    try:
        result = cognito.sign_up(
            ClientId=SECRETS["COGNITO_APP_CLIENT_ID"],
            Username=email,
            Password=password,
            UserAttributes=[
                {"Name": "email", "Value": email},
            ],
        )
    # todo Cognito에 있는데 DB에 없는 경우 지우고 다시 만들어서 정상 처리하게 해줘야 함
    except cognito.exceptions.UsernameExistsException:
        # todo DB에 유저 있는 경우가 409 응답
        raise HTTPException(status_code=409)
    except cognito.exceptions.InvalidParameterException:
        raise HTTPException(status_code=400)
    return {"user_id": result["UserSub"]}


@router.get("/user/country", tags=[API_PREFIX])
async def get_user_country(request: Request):
    handler = ipinfo.getHandlerAsync(SECRETS["IPINFO_API_KEY"])
    try:
        client_info = await handler.getDetails(request.client.host)
        return {"country": client_info.country, "timezone": client_info.timezone}
    except AttributeError:  # localhost(테스트)인 경우
        default = {"country": "KR", "timezone": "Asia/Seoul"}
        log.warning(
            "GET /user/country"
            f"\n국가 정보 취득에 실패했습니다. 기본값을 응답합니다."
            f"\nIP: {request.client.host} , 응답된 기본값: {default}"
        )
        return default
    finally:
        await handler.deinit()
