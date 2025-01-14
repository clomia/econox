"""
- /api/feature/... 
- feature를 다루는 기능을 제공합니다. ( user <-> element <-> factor )
"""

import re
import random
import asyncio
from math import ceil
from typing import Literal, List
from collections import defaultdict

import psycopg
from pydantic import BaseModel, constr, validator
from fastapi import HTTPException, Query

from backend import db
from backend.calc import datetime2utcstr, utcstr2datetime
from backend.http import APIRouter
from backend.integrate import get_element, get_name

router = APIRouter("feature")

ele_section_type = Literal["symbol", "country", "custom"]


@router.basic.post("/user/element")
async def insert_element_to_user(
    code: constr(min_length=1),
    section: ele_section_type,
    user=router.basic.user,
):
    """엘리먼트를 유저에게 저장합니다."""
    await get_element(section, code)  # 실제 존재하는 엘리먼트인지 검증

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
async def delete_element_from_user(
    code: constr(min_length=1),
    section: ele_section_type,
    user=router.basic.user,
):
    # Element 검증은 저장할때 하므로 삭제할떄는 필요없음
    """
    - 엘리먼트를 유저에게서 삭제합니다.
    - 실제 삭제 여부와 무관하게 결과적으로 해당 요소가 유저에게 없는 경우 성공 응답을 합니다.
    """
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
    # 실제로 삭제 동작을 했는지는 모르지만 결과가 무결하므로 200 응답
    return {"message": f"As a result, {code} element does not exist in user"}


@router.basic.get("/user/elements")
async def get_elements_from_user(
    lang: str = Query(..., min_length=2, max_length=2),
    user=router.basic.user,
):
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
        # DB에서 나온 데이터이므로 여기에서 에러나면 서버 문제임!
        ele = await get_element(section=record["section"], code=record["code"])
        name, note = await asyncio.gather(ele.name.en(), ele.note.trans(to=lang))
        return {
            "code": record["code"],
            "section": record["section"],
            "name": name,
            "note": note,
            "update": datetime2utcstr(record["created"]),
        }

    return await asyncio.gather(*[parsing(record) for record in fetched])


@router.basic.get("/element/factors")
async def get_factors_from_element(
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

    element = await get_element(element_section, element_code)
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
        "SELECT * FROM elements WHERE section={s} AND code={c}",
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


class FeatureGroupInit(BaseModel):
    name: constr(min_length=1, max_length=200)  # DB->VARCHAR(255)
    description: str = ""


@router.basic.post("/group")
async def create_feature_group_to_user(
    item: FeatureGroupInit,
    user=router.basic.user,
):
    """유저에게 피쳐 그룹을 생성하고 그룹 아이디를 응답합니다."""
    feature_group = await db.InsertSQL(
        table="feature_groups",
        returning=True,
        user_id=user["id"],
        name=item.name.strip(),
        description=item.description,
    ).exec()
    return {"message": f"Feature group created", "group_id": feature_group["id"]}


class FeatureGroupUpdate(BaseModel):
    group_id: int
    name: constr(min_length=1) | None = None
    description: str | None = None
    chart_type: constr(min_length=1) | None = None
    public: bool | None = None


@router.basic.patch("/group")
async def update_feature_group(item: FeatureGroupUpdate, user=router.basic.user):
    """
    - 피쳐 그룹의 정보를 업데이트합니다.
    - 요청 본문에 group_id 명시 후 업데이트하고자 하는 필드만 정의해주세요.
        - 업데이트 가능 필드: name, description, chart_type, public
    - 유저가 소유하지 않은 피쳐 그룹에 대해서는 200을 응답하지만, 아무런 변화도 일어나지 않습니다.
    """
    db_params = dict(item)
    values = ""
    if item.name is not None:
        values += "name={name},"
        db_params["name"] = item.name.strip()
    if item.description is not None:
        values += "description={description},"
    if item.chart_type is not None:
        values += "chart_type={chart_type},"
    if item.public is not None:
        values += "public={public},"
    values = values.rstrip(",")
    await db.SQL(
        f"UPDATE feature_groups SET {values} WHERE "
        "id={group_id} AND user_id={user_id}",
        params=dict(item) | {"user_id": user["id"]},
    ).exec()
    return {"message": f"Feature group({item.group_id}) update complete"}


@router.basic.delete("/group")
async def delete_feature_group_from_user(group_id: int, user=router.basic.user):
    """
    - 유저에게서 피쳐 그룹을 제거합니다.
    - 유저가 소유하지 않은 피쳐 그룹에 대해서도 200을 응답하지만, 제거되지 않습니다.
    """
    await db.SQL(
        "DELETE FROM feature_groups WHERE id={group_id} AND user_id={user_id}",
        params={"group_id": group_id, "user_id": user["id"]},
    ).exec()
    return {"message": "Request processed"}


class ElementProperty(BaseModel):
    section: ele_section_type
    code: constr(min_length=1)


class FactorProperty(BaseModel):
    section: constr(min_length=1)
    code: constr(min_length=1)


class FeatureGroup(BaseModel):
    id: int
    created: str
    name: str
    description: str
    chart_type: str
    public: bool

    class Feature(BaseModel):
        added: str
        color: str

        class Name(BaseModel):
            element: str
            factor_section: str
            factor: str

        element: ElementProperty
        factor: FactorProperty
        name: Name

    features: List[Feature]


@router.basic.get("/groups")
async def get_feature_groups_from_user(
    lang: str = Query(..., min_length=2, max_length=2),
    user=router.basic.user,
) -> List[FeatureGroup]:
    """
    - 유저가 소유한 모든 피쳐 그룹과 피쳐 그룹에 속한 모든 피쳐를 응답합니다.
    - 모든 배열은 요소의 생성, 수정 날짜에 따라 정렬되어 있습니다.
        - 최근에 변경된 것이 앞으로 오도록
    """
    query = """
    SELECT 
        fg.id AS group_id,
        fg.name AS group_name,
        fg.description AS group_description,
        fg.chart_type AS group_chart_type,
        fg.public AS group_public,
        fg.created AS group_created,
        fgf.feature_color AS group_feature_color,
        fgf.created AS group_feature_created,
        e.section AS feature_element_section,
        e.code AS feature_element_code,
        f.section AS feature_factor_section,
        f.code AS feature_factor_code
    FROM feature_groups fg
    LEFT JOIN feature_groups_features fgf ON fg.id = fgf.feature_group_id
    LEFT JOIN elements_factors ef ON fgf.feature_id = ef.id
    LEFT JOIN elements e ON ef.element_id = e.id
    LEFT JOIN factors f ON ef.factor_id = f.id
    WHERE fg.user_id = {user_id}
    """
    features = await db.SQL(query, params={"user_id": user["id"]}, fetch="all").exec()

    def get_key(feature):
        """feature를 나타내는 고유 불변 객체"""
        return (
            feature["feature_element_section"],
            feature["feature_element_code"],
            feature["feature_factor_section"],
            feature["feature_factor_code"],
        )

    namekeys = {
        get_key(feature)
        for feature in features  # 중복제거 & 빈 그룹 제거
        if feature["group_feature_created"] is not None
    }

    async def _get_name(key: tuple):  # gather 사용을 위해 wrapper로 재정의
        return (key, await get_name(lang, *key))

    namelist = await asyncio.gather(*[_get_name(key) for key in namekeys])
    names = {key: data for key, data in namelist}

    tree = defaultdict(dict)
    for feature in features:
        group_id = feature["group_id"]

        tree[group_id]["created"] = datetime2utcstr(feature["group_created"])
        tree[group_id]["name"] = feature["group_name"]
        tree[group_id]["description"] = feature["group_description"]
        tree[group_id]["chart_type"] = feature["group_chart_type"]
        tree[group_id]["public"] = feature["group_public"]

        if tree[group_id].get("features") is None:
            tree[group_id]["features"] = []
        if feature["group_feature_created"] is None:
            continue  # 피쳐 그룹에 아무런 피쳐도 없는 경우이다.
        tree[group_id]["features"].append(
            {
                "added": datetime2utcstr(feature["group_feature_created"]),
                "color": feature["group_feature_color"],
                "element": {
                    "section": feature["feature_element_section"],
                    "code": feature["feature_element_code"],
                },
                "factor": {
                    "section": feature["feature_factor_section"],
                    "code": feature["feature_factor_code"],
                },
                "name": names[get_key(feature)],
            }
        )

    array = [{"id": group_id} | tree[group_id] for group_id in tree.keys()]
    array.sort(key=lambda group: utcstr2datetime(group["created"]), reverse=True)

    for group in array:  # 모든 그룹에 대해 피쳐를 추가한 날짜 순으로 정렬
        group["features"].sort(
            key=lambda ft: utcstr2datetime(ft["added"]), reverse=True
        )

    return array


class GroupFeature(BaseModel):
    """그룹에 속한 피쳐 정의"""

    group_id: int
    element: ElementProperty
    factor: FactorProperty


color_palette = [
    "rgb(60,100,255)",
    "rgb(225, 170, 54)",
    "rgb(240, 244, 250)",
    "rgb(255, 252, 44)",
    "rgb(170, 128, 234)",
    "rgb(1,245,178)",
    "rgb(250, 160, 244)",
    "rgb(255, 200, 90)",
    "rgb(250, 110, 200)",
]


@router.basic.post("/group/feature")
async def insert_feature_to_feature_group(item: GroupFeature, user=router.basic.user):
    """
    - 피쳐 그룹에 피쳐를 추가합니다.
    - 유저가 소유하지 않은 피쳐 그룹이거나 유효하지 않은 피쳐에 대해서도 200을 응답하나, 아무런 동작도 하지 않습니다.
        - 이 API는 실제로 시계열 데이터 수집에 성공했던 피쳐만 다룹니다.
        - 이 API를 사용하기 전에 별도의 데이터 조회 API를 통해 유효한 피쳐인지 확인하세요.
    - 이미 그룹에 존재하는 피쳐를 중복하여 추가하는 요청에는 409 에러를 응답합니다.
    """

    features = await db.SQL(
        "SELECT * FROM feature_groups_features WHERE feature_group_id={group_id}",
        params={"group_id": item.group_id},
        fetch="all",
    ).exec()
    # 피쳐 색상을 설정하기 위해 기존에 할당된 모든 색을 불러옵니다.
    exist_colors = [feature["feature_color"] for feature in features]
    available_colors = [color for color in color_palette if color not in exist_colors]
    color = available_colors[0] if available_colors else random.choice(color_palette)

    insert_query = """
    INSERT INTO feature_groups_features (feature_group_id, feature_color, feature_id)
    SELECT {group_id}, {color}, ef.id
    FROM elements e
    JOIN factors f ON e.section = {ele_section} AND e.code = {ele_code}
    JOIN elements_factors ef ON ef.element_id = e.id AND ef.factor_id = f.id
    WHERE f.section = {fac_section} AND f.code = {fac_code}
    AND EXISTS (
        SELECT 1
        FROM feature_groups
        WHERE id = {group_id} AND user_id = {user_id}
    )
    """  # EXISTS 조건에서 유저의 그룹 소유권을 확인합니다.
    sql = db.SQL(
        insert_query,
        params={
            "user_id": user["id"],
            "group_id": item.group_id,
            "color": color,
            "ele_section": item.element.section,
            "ele_code": item.element.code,
            "fac_section": item.factor.section,
            "fac_code": item.factor.code,
        },
    )
    try:
        await sql.exec()
    except psycopg.errors.UniqueViolation:
        raise HTTPException(
            status_code=409, detail="The feature already exists in the group"
        )

    return {"message": f"Feature has been added to the feature group({item.group_id})"}


class GroupFeatureUpdateTarget(BaseModel):
    color: str

    @validator("color")
    def validate_color(cls, v):
        """color는 rgb 형식의 CSS 호환 문자열만 허용됩니다."""
        pattern = r"rgb\(\s*(\d{1,3})\s*,\s*(\d{1,3})\s*,\s*(\d{1,3})\s*\)"
        if not re.match(pattern, v):
            raise ValueError("Invalid RGB color format")
        r, g, b = map(int, re.match(pattern, v).groups())
        if not all(0 <= val <= 255 for val in [r, g, b]):
            raise ValueError("RGB values must be between 0 and 255")
        return v


class GroupFeatureUpdate(GroupFeature):
    target: GroupFeatureUpdateTarget


@router.basic.patch("/group/feature")  # 변경 가능한 부분은 color밖에 없음
async def update_feature_from_feature_group(
    item: GroupFeatureUpdate, user=router.basic.user
):
    """
    - 피쳐 그룹에 속한 피쳐의 속성을 변경합니다.
        - 변경 가능한 유일한 속성은 color 입니다.
    - 유저가 소유하지 않은 피쳐 그룹이거나 유효하지 않은 피쳐에 대해서도 200을 응답하나, 아무런 동작도 하지 않습니다.
    """
    query = """
    UPDATE feature_groups_features
    SET feature_color = {color}
    WHERE feature_group_id IN (
        SELECT id
        FROM feature_groups
        WHERE user_id = {user_id}
    )
    AND feature_id = (
        SELECT ef.id
        FROM elements_factors ef
        JOIN elements e ON ef.element_id = e.id
        JOIN factors f ON ef.factor_id = f.id
        WHERE e.section = {element_section}
        AND e.code = {element_code}
        AND f.section = {factor_section}
        AND f.code = {factor_code}
    )
    """  # IN 조건절에서 유저의 피쳐 그룹 소유권을 확인합니다.
    await db.SQL(
        query,
        params={
            "color": item.target.color,
            "user_id": user["id"],
            "element_section": item.element.section,
            "element_code": item.element.code,
            "factor_section": item.factor.section,
            "factor_code": item.factor.code,
        },
    ).exec()
    return {"message": "update completed"}


@router.basic.delete("/group/feature")
async def delete_feature_from_feature_group(item: GroupFeature, user=router.basic.user):
    """
    - 피쳐 그룹에서 피쳐를 제거합니다.
    - 유저가 소유하지 않은 피쳐 그룹에 대해서도 200을 응답하지만, 실제로 동작하지 않습니다.
    """
    await db.SQL(
        """
        DELETE FROM feature_groups_features
        WHERE feature_id IN (
            SELECT ef.id
            FROM elements_factors ef
            JOIN elements e ON ef.element_id = e.id
            JOIN factors f ON ef.factor_id = f.id
            WHERE e.section = {element_section} AND e.code = {element_code}
            AND f.section = {factor_section} AND f.code = {factor_code}
        )
        AND feature_group_id IN (
            SELECT fg.id
            FROM feature_groups fg
            WHERE fg.id = {feature_group_id} AND fg.user_id = {user_id}
        )""",
        params={
            "user_id": user["id"],
            "feature_group_id": item.group_id,
            "element_section": item.element.section,
            "element_code": item.element.code,
            "factor_section": item.factor.section,
            "factor_code": item.factor.code,
        },
    ).exec()
    return {"message": "Request processed"}
