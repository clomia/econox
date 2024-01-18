"""
- api와 data 모듈의 통합 로직 중 반복되는 부분을 함수로 제공합니다.
"""
import io

import xarray as xr
import pandas as pd
from fastapi import HTTPException, Request
from fastapi.responses import JSONResponse

from backend.data import fmp, world_bank
from backend.data.model import Factor
from backend.data.exceptions import ElementDoesNotExist, LanguageNotSupported
from backend.math import denormalize


async def lang_exception_handler(request: Request, call_next):
    """
    - LanguageNotSupported 예외를 422 HTTPException 예외로 전파시킵니다.
    - app.py에서 FastAPI 앱에 미들웨어로 등록되었습니다.
    """
    try:
        return await call_next(request)
    except LanguageNotSupported as e:
        return JSONResponse(status_code=422, content=e.message)


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


class Feature:
    """
    - featrue 시계열을 읽고 변환하는 기능을 제공하며 예외를 적절한 HTTPException로 전파시킵니다.
    - API 함수에서 즉시 사용 가능한 시계열 데이터 불러오기 로직을 제공합니다.
    """

    def __init__(
        self,
        element_section: str,
        element_code: str,
        factor_section: str,
        factor_code: str,
    ):
        self.element_section = element_section
        self.element_code = element_code
        self.factor_section = factor_section
        self.factor_code = factor_code

    async def get(self) -> xr.Dataset:
        element = await get_element(self.element_section, self.element_code)
        # ClientMeta 메타클래스가 만든 data_class 클래스의 인스턴스
        try:
            data_instance = getattr(element, element.attr_name[self.factor_section])
            factor: Factor = getattr(data_instance, self.factor_code)
        except KeyError:
            raise HTTPException(
                status_code=404,
                detail=f"factor_section {self.factor_section} does not exist",
            )
        except AttributeError:
            raise HTTPException(
                status_code=404, detail=f"factor_code {self.factor_code} does not exist"
            )

        return await factor.get()

    async def to_dataframe(self, normalized: bool = False) -> pd.DataFrame:
        """
        - 인덱스와 time, value 컬럼을 가진 dataframe을 반환합니다.
        """
        data_set = await self.get()
        data_array = data_set.daily if normalized else denormalize(data_set)
        data_frame = data_array.to_dataframe().reset_index()
        data_frame.columns = ["time", "value"]
        data_frame.index.name = "index"
        return data_frame

    async def to_csv(self, normalized: bool = False) -> bytes:
        """
        - normalized: 정규화 여부
        - return: 파일 데이터를 bytes로 반환합니다. 디스크를 사용하지 않습니다.
        """
        data_frame = await self.to_dataframe(normalized)
        data_frame.to_csv(buffer := io.BytesIO())
        return buffer.getvalue()

    async def to_xlsx(self, normalized: bool = False) -> bytes:
        """
        - normalized: 정규화 여부
        - return: 파일 데이터를 bytes로 반환합니다. 디스크를 사용하지 않습니다.
        """
        data_frame = await self.to_dataframe(normalized)
        sheet_name = f"econox"
        with pd.ExcelWriter(
            buffer := io.BytesIO(), date_format="YYYY-MM-DD", engine="openpyxl"
        ) as writer:
            data_frame.to_excel(writer, sheet_name=sheet_name)
            sheet = writer.sheets[sheet_name]
            # 컬럼 길이가 글자 길이보다 작으면 깨지므로 여유롭게 설정
            sheet.column_dimensions["B"].width = 15
            sheet.column_dimensions["C"].width = 23
        return buffer.getvalue()
