"""
- api와 data 모듈의 통합 로직 중 반복되는 부분을 함수로 제공합니다.
"""
import xarray as xr
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from backend.data import fmp, world_bank
from backend.data.model import Factor
from backend.data.exceptions import ElementDoesNotExist, LanguageNotSupported


async def get_element(section: str, code: str):
    """Element를 가져옵니다. 존재하지 않는 경우 적절한 HTTPException을 발생시킵니다."""
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


async def get_feature(
    element_section: str, element_code: str, factor_section: str, factor_code: str
) -> xr.Dataset | None:
    """
    - Element의 Factor를 가져옵니다.
    - 잘못된 Feature인 경우 적절한 HTTPException을 발생시킵니다.
        - 함수 매개변수가 잘못된 경우입니다.
    - 데이터가 비어있는 경우 None을 반환합니다.
        - 올바른 매개변수이지만 데이터를 찾지 못한 경우입니다.
    """
    element = await get_element(element_section, element_code)
    # ClientMeta 메타클래스가 만든 data_class 클래스의 인스턴스
    try:
        data_instance = getattr(element, element.attr_name[factor_section])
        factor: Factor = getattr(data_instance, factor_code)
    except KeyError:
        raise HTTPException(
            status_code=404, detail=f"factor_section {factor_section} does not exist"
        )
    except AttributeError:
        raise HTTPException(
            status_code=404, detail=f"factor_code {factor_code} does not exist"
        )

    return await factor.get()


async def lang_exception_handler(request: Request, call_next):
    """
    - LanguageNotSupported 예외를 422 HTTPException 예외로 전파시킵니다.
    - app.py에서 FastAPI 앱에 미들웨어로 등록되었습니다.
    """
    try:
        return await call_next(request)
    except LanguageNotSupported as e:
        return JSONResponse(status_code=422, content=e.message)
