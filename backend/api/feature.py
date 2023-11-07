""" /api/data """
from typing import Literal

from pydantic import BaseModel, constr

from backend import db
from backend.http import APIRouter

router = APIRouter("feature")


class Element(BaseModel):
    code_type: constr(min_length=1)
    code: constr(min_length=1)


@router.basic.post("/element/user")
async def insert_selected_element(item: Element, user=router.basic.auth):
    """Element를 생성, 유저와 연결"""
    db_transaction = db.Transaction()
    db_transaction.append(  # elements가 없다면 생성
        """
        INSERT INTO elements (code_type, code)
        VALUES ({code_type}, {code})
        ON CONFLICT (code_type, code) DO NOTHING
        """,
        code_type=item.code_type,
        code=item.code,
    )
    db_transaction.append(  # 유저에 element 연결
        """
        INSERT INTO users_elements (user_id, element_id)
        VALUES (
            {user_id},
            (SELECT id FROM elements WHERE code_type={code_type} and code={code})
        )""",
        user_id=user["id"],
        code_type=item.code_type,
        code=item.code,
    )
    await db_transaction.exec()
    return {}
