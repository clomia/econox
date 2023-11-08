""" /api/data """
from typing import Literal

import psycopg
from pydantic import BaseModel, constr
from fastapi import HTTPException

from backend import db
from backend.math import datetime2utcstr
from backend.http import APIRouter

router = APIRouter("feature")


class Element(BaseModel):
    code_type: Literal["symbol", "country"]
    code: constr(min_length=1)


@router.basic.post("/user/element")
async def insert_element_to_user(item: Element, user=router.basic.auth):
    """엘리먼트를 유저에게 저장합니다."""
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
    try:
        await db_transaction.exec()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(
            status_code=409, detail=f"User already has {item.code_type} {item.code}"
        )
    return {"message": f"User inserts element {item.code_type} {item.code}"}


@router.basic.get("/user/elements")
async def get_element_from_user(user=router.basic.auth):
    """유저에게 저장된 엘리먼트들을 가져옵니다."""
    elements = await db.exec(
        """
    SELECT e.code, e.code_type, ue.created
    FROM elements e
    INNER JOIN users_elements ue ON ue.element_id = e.id
    WHERE ue.user_id = {user_id}
    ORDER BY ue.created DESC;
    """,
        params={"user_id": user["id"]},
    )
    return [
        {"code": code, "code_type": code_type, "update": datetime2utcstr(update_time)}
        for code, code_type, update_time in elements
    ]
