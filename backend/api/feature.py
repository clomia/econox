""" /api/data """
import asyncio
from math import ceil
from typing import Literal

import psycopg
from pydantic import constr
from fastapi import HTTPException, Query

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


@router.basic.get("/factors")
async def get_factor_from_element(
    element_code: str,
    element_section: str,
    lang: str = Query(..., min_length=2, max_length=2),  # ISO Alpha-2 (2글자만 허용)
    page: int = Query(1, gt=0),  # 1 이상만 허용
):
    """
    - Element에 속한 펙터들을 가져옵니다.
    - lang: 응답 데이터의 언어 (ISO 639-1)
    - page: 가져올 페이지 지정
        - 페이지당 20개의 펙터를 포함하며 범위를 벗어나면 빈 배열을 응답합니다.
    - response: 총 페이지 갯수와 펙터 배열을 응답합니다.
    """

    per_page = 20
    page_offset = (page - 1) * per_page

    async def translate(factor: dict):
        """
        - 펙터의 다국어객체를 번역해서 직렬화 가능한 dict로 변환
        - factor: element의 factors 메서드를 통해 얻은 펙터 하나
        """

        factor_name, factor_note, section_name, section_note = await asyncio.gather(
            factor["name"].trans(to=lang),
            factor["note"].trans(to=lang),
            factor["section"]["name"].trans(to=lang),
            factor["section"]["note"].trans(to=lang),
        )
        return {
            "code": factor["code"],
            "name": factor_name,
            "note": factor_note,
            "section": {
                "code": factor["section"]["code"],
                "name": section_name,
                "note": section_note,
            },
        }

    if element_section == "symbol":
        element = await fmp.Symbol(element_code).load()
    elif element_section == "country":
        element = await world_bank.Country(element_code).load()
    all_factors = element.factors()

    sql = db.SQL(
        """
        SELECT f.*
        FROM elements e
        INNER JOIN elements_factors ef ON e.id = ef.element_id
        INNER JOIN factors f ON ef.factor_id = f.id
        WHERE e.code = {code} AND e.section = {section} """,
        params={"code": element_code, "section": element_section},
        fetch="all",
    )
    fetched = await sql.exec()

    if fetched:  # 해당하는 펙터만 정제해서 응답
        target = []
        db_factors = [(fac["section"], fac["code"]) for fac in fetched]
        for factor in all_factors:
            if (factor["section"]["code"], factor["code"]) in db_factors:
                target.append(factor)
        target_page = target[page_offset : page_offset + per_page]
        # translate 할 수 있는 횟수에 한계가 있으므로 pagenation 해야 함
        pages = ceil(len(target) / per_page)
        factors = await asyncio.gather(*[translate(factor) for factor in target_page])
        return {"factors": factors, "pages": pages}

    # ==================== DB 셋업 시작 ====================
    # 필요한 Element와 Factor들이 모두 있도록 한 후 연결합니다. 약 10초 소요됩니다.

    await db.SQL(  # Element 없으면 생성
        """
        INSERT INTO elements (section, code) 
        VALUES ({section}, {code})
        ON CONFLICT (section, code) DO NOTHING """,
        params={"section": element_section, "code": element_code},
    ).exec()
    db_element = await db.SQL(  # Element ID 가져오기
        "SELECT * FROM elements WHERE section={s} and code={c}",
        {"s": element_section, "c": element_code},
        fetch="one",
    ).exec()

    codes, names, notes, sections = [], [], [], []
    for factor in all_factors:
        codes.append(factor["code"])
        names.append(await factor["name"].en())
        notes.append(await factor["note"].en())
        sections.append(factor["section"]["code"])

    await db.ManyInsertSQL(  # Factors 없으면 생성
        "factors",
        params={
            "code": codes,
            "name": names,
            "note": notes,
            "section": sections,
        },
        conflict_pass=["section", "code"],
    ).exec()

    query = "SELECT * FROM factors WHERE "
    query += " OR ".join(  # Factors ID 가져오기
        [f"(section = '{sec}' AND code = '{co}')" for sec, co in zip(sections, codes)]
    )  # factors는 서버 내부에서 입력하는거라 파라미터화 안해도 됌
    db_factors = await db.SQL(query, fetch="all").exec()

    await db.ManyInsertSQL(  # Element에 Factors모두 연결
        "elements_factors",
        params={
            "element_id": [int(db_element["id"])] * len(db_factors),
            "factor_id": [int(db_factor["id"]) for db_factor in db_factors],
        },
        conflict_pass=["element_id", "factor_id"],
    ).exec()
    # ==================== DB 셋업 종료 ====================
    target = all_factors[page_offset : page_offset + per_page]
    pages = ceil(len(all_factors) / per_page)
    factors = await asyncio.gather(*[translate(factor) for factor in target])
    return {"factors": factors, "pages": pages}
