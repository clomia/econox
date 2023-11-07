""" /api/data """
from typing import Literal

from pydantic import BaseModel, Field, constr

from backend.http import APIRouter

router = APIRouter("feature")


class Element(BaseModel):
    # 요청받은 JSON에서는 type, Python코드 안에서는 _type을 사용
    _type: Literal["symbol", "country"] = Field(..., alias="type")
    code: str = constr(min_length=1)

    class Config:
        allow_population_by_field_name = True


@router.basic.post("/elements")
async def insert_selected_element(item: Element):
    "INSERT INTO elements (type, code)"
