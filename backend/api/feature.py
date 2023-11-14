""" /api/data """
from typing import Literal

import psycopg
from pydantic import BaseModel, constr
from fastapi import HTTPException

from backend import db
from backend.math import datetime2utcstr
from backend.http import APIRouter

router = APIRouter("feature")


@router.basic.post("/user/element")
async def insert_element_to_user(
    code: constr(min_length=1),
    code_type: Literal["symbol", "country"],
    user=router.basic.auth,
):
    """엘리먼트를 유저에게 저장합니다."""
    db_transaction = db.Transaction()
    db_transaction.append(  # elements가 없다면 생성
        """
        INSERT INTO elements (code_type, code)
        VALUES ({code_type}, {code})
        ON CONFLICT (code_type, code) DO NOTHING
        """,
        code_type=code_type,
        code=code,
    )
    db_transaction.append(  # 유저에 element 연결
        """
        INSERT INTO users_elements (user_id, element_id)
        VALUES (
            {user_id},
            (SELECT id FROM elements WHERE code_type={code_type} and code={code})
        )""",
        user_id=user["id"],
        code_type=code_type,
        code=code,
    )
    try:
        await db_transaction.exec(silent=True)  # 아래 에러는 의도된거라 로그 안떠도 됌
    except psycopg.errors.UniqueViolation:
        raise HTTPException(
            status_code=409, detail=f"User already has {code_type} {code}"
        )
    return {"message": f"Insert element {code_type} {code} to user"}


@router.basic.delete("/user/element")
async def insert_element_to_user(
    code: constr(min_length=1),
    code_type: Literal["symbol", "country"],
    user=router.basic.auth,
):
    """엘리먼트를 유저에게서 삭제합니다."""
    await db.exec(
        """
        DELETE FROM users_elements
        USING elements
        WHERE users_elements.element_id = elements.id
        AND users_elements.user_id = {user_id}
        AND elements.code_type = {code_type}
        AND elements.code = {code}
        """,
        params={"user_id": user["id"], "code_type": code_type, "code": code},
    )
    return {"message": "Delete successfully"}  # 실제로 삭제 동작을 했는지는 모름, 결과가 무결하므로 200 응답


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
