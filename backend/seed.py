"""
- 새롭게 회원가입 한 유저를 위해 초기 샘플 데이터를 세팅해주는 함수를 구현합니다.
- 현재는 기술적 난이도로 인해 단변량 툴을 세팅해주는 로직만 구현하였습니다.
- 추후 다변량 툴까지 세팅해주도록 고도화 할 예정입니다.
"""

from backend import db

symbols = [
    "AAPL",
    "MSFT",
    "GOOGL",
    "TSLA",
    "NKE",
    "NFLX",
    "ABNB",
    "UBER",
    "BLDR",
    "MET",
]


async def seed_sample_data(user_id: str):
    """
    - 초기 샘플 데이터를 새팅해줍니다.
    - 회원가입 유저를 대상으로 사용하세요.
    """
    # 모든 요소가 테이블에 존재하도록 보장
    await db.ManyInsertSQL(
        "elements",
        params={
            "section": ["symbol" for _ in symbols],
            "code": [code for code in symbols],
        },
        conflict_pass=["section", "code"],
    ).exec()

    sqls = []
    for code in symbols:
        sqls.append(
            db.SQL(
                """
            INSERT INTO users_elements (user_id, element_id)
            VALUES (
                {user_id},
                (SELECT id FROM elements WHERE section='symbol' and code={code})
            )""",
                params={"user_id": user_id, "code": code},
            )
        )
    await db.exec(*sqls)
