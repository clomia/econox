""" /api/data """
import asyncio
from typing import Literal

import psycopg
from pydantic import constr
from fastapi import HTTPException

from backend import db
from backend.data import fmp, world_bank
from backend.math import datetime2utcstr
from backend.http import APIRouter

router = APIRouter("feature")

section_type = Literal["symbol", "country", "custom"]


@router.basic.post("/user/element")
async def insert_element_to_user(
    code: constr(min_length=1),
    section: section_type,
    user=router.basic.user,
):
    """엘리먼트를 유저에게 저장합니다."""
    insert_element_if_it_does_not_exist = db.SQL(
        """
        INSERT INTO elements (section, code)
        VALUES ({section}, {code})
        ON CONFLICT (section, code) DO NOTHING
        """,
        params={"section": section, "code": code},
    )
    create_connection = db.SQL(
        """
        INSERT INTO users_elements (user_id, element_id)
        VALUES (
            {user_id},
            (SELECT id FROM elements WHERE section={section} and code={code})
        )""",
        params={"user_id": user["id"], "section": section, "code": code},
    )
    try:
        await db.exec(insert_element_if_it_does_not_exist, create_connection)
    except psycopg.errors.UniqueViolation:
        raise HTTPException(
            status_code=409, detail=f"User already has {section} {code}"
        )
    return {"message": f"Insert element {section} {code} to user"}


@router.basic.delete("/user/element")
async def insert_element_to_user(
    code: constr(min_length=1),
    section: section_type,
    user=router.basic.user,
):
    """엘리먼트를 유저에게서 삭제합니다."""
    query = """
        DELETE FROM users_elements
        USING elements
        WHERE users_elements.element_id = elements.id
        AND users_elements.user_id = {user_id}
        AND elements.section = {section}
        AND elements.code = {code}
    """
    params = {"user_id": user["id"], "section": section, "code": code}
    await db.SQL(query, params).exec()
    return {"message": "Delete successfully"}  # 실제로 삭제 동작을 했는지는 모르지만 결과가 무결하므로 200 응답


@router.basic.get("/user/elements")
async def get_element_from_user(lang: str, user=router.basic.user):
    """
    - 유저에게 저장된 엘리먼트들을 가져옵니다.
    - lang: 응답 데이터의 언어 (ISO 639-1)
    """
    query = """
        SELECT e.code, e.section, ue.created
        FROM elements e
        INNER JOIN users_elements ue ON ue.element_id = e.id
        WHERE ue.user_id = {user_id}
        ORDER BY ue.created DESC """  # 최신의 것이 앞으로 오도록 정렬
    fetched = await db.SQL(query, params={"user_id": user["id"]}, fetch="all").exec()

    async def parsing(record: dict):
        # 캐싱되어있으면 엄청 빠름
        if record["section"] == "symbol":
            ele = await fmp.Symbol(record["code"]).load()
        elif record["section"] == "country":
            ele = await world_bank.Country(record["code"]).load()
        name, note = await asyncio.gather(ele.name.en(), ele.note.trans(to=lang))
        return {
            "code": record["code"],
            "section": record["section"],
            "name": name,
            "note": note,
            "update": datetime2utcstr(record["created"]),
        }

    return await asyncio.gather(*[parsing(record) for record in fetched])
