"""
- api와 data 모듈의 통합 로직 중 반복되는 부분을 함수로 제공합니다.
"""
from fastapi import HTTPException

from backend.data import fmp, world_bank
from backend.data.exceptions import ElementDoesNotExist


async def get_element(section: str, code: str):
    """Element를 가져옵니다. 존재하지 않는 경우 적절한 HTTPException 를 발생시킵니다."""
    try:
        if section == "symbol":
            element = await fmp.Symbol(code).load()
        elif section == "country":
            element = await world_bank.Country(code).load()
        else:
            raise HTTPException(
                status_code=422,
                detail=f"element_section {section} is not supported.",
            )
    except ElementDoesNotExist as e:
        raise HTTPException(status_code=404, detail=e.message)
    else:
        return element


# async def translate_exception_handler 미들웨어...(translate):
