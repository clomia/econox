"""
- api와 data 모듈의 통합 로직 중 반복되는 부분을 함수로 제공합니다.
"""

from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from backend.data import fmp, world_bank
from backend.data.exceptions import ElementDoesNotExist, LanguageNotSupported


async def get_element(section: str, code: str):
    """Element를 가져옵니다. 존재하지 않는 경우 적절한 HTTPException 를 발생시킵니다."""
    try:
        if section == "symbol":
            element = await fmp.Symbol(code).load()
        elif section == "country":
            element = await world_bank.Country(code).load()
        else:
            raise HTTPException(
                status_code=404,
                detail=f"element_section {section} does not exist",
            )
    except ElementDoesNotExist as e:
        raise HTTPException(status_code=404, detail=e.message)
    else:
        return element


async def lang_exception_handler(request: Request, call_next):
    """
    - LanguageNotSupported 예외를 422 HTTPException 예외로 전파시킵니다.
    - app.py에서 FastAPI 앱에 미들웨어로 등록되었습니다.
    """
    try:
        return await call_next(request)
    except LanguageNotSupported as e:
        return JSONResponse(status_code=422, content=e.message)
