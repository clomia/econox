"""
```
# 1. 단일 쿼리 실행하기
sql = db.SQL("SELECT * FROM elements WHERE code={code}", params={"code": "AAPLE"})
element = await sql.exec()
print(element) # {'id': 8, 'section': 'country', 'code': 'AAPLE'}

# 2. 여러 SQL을 하나의 트렌젝션으로 실행하기
read_sql = db.SQL("SELECT * FROM elements WHERE code={code}", params={"code": "AAPLE"})
write_sql = db.SQL(
    "INSERT INTO elements (section, code) VALUES ({section}, {code})",
    params={"section": "country", "code": "USA"},
    fetch=False,
)
fetched = await db.exec(read_sql, write_sql)
element = fetched[read_sql]
print(element) # {'id': 8, 'section': 'country', 'code': 'AAPLE'}
```
- SQL 클래스를 사용해서 단일 쿼리를 정의하세요.
    - INSERT 쿼리는 SQL의 하위클래스인 InsertSQL를 사용하여 간결하게 정의하세요.
- exec 함수를 사용해서 쿼리를 실행하세요.
    - SQL 객체의 exec 메서드를 통해 단일 쿼리를 실행할 수 있습니다.
    - 모듈에 정의된 exec 함수를 통해 여러 쿼리를 단일 트렌젝션으로 실행할 수 있습니다.
- psycopg 클라이언트 예외 처리 
    - psycopg 에러를 통해 DB의 응답을 구분하세요
    - __cause__ 속성을 통해 QueryError 객체에 접근할 수 있습니다.
    - QueryError의 sql 속성을 통해 실행된 SQL 객체에 접근할 수 있습니다.
"""
from __future__ import annotations

import re
import json
import asyncio
from typing import List, Tuple, Dict, Any, Literal

import boto3
import psycopg
from psycopg.rows import dict_row

from backend.system import SECRETS, log

# ======== 쿼리 실행 함수 =========


class QueryError(Exception):
    def __init__(self, sql: SQL, msg: str = ""):
        self.sql = sql
        super().__init__(f"[DB Error] {sql} {msg}")


async def exec(
    *sql: SQL,
    dbname: str = "econox",
    _retry=False,
) -> Dict[SQL, None | List[Dict[str, Any]]]:
    """
    - 여러 SQL을 동시에 실행합니다. 하나의 트렌젝션으로 취급되며 하나라도 실패하면 모두 안전하게 롤백됩니다.
    - retuen: SQL에 대한 결과가 딕셔너리로 매핑되어 반환됩니다.
        - 그리고 결과는 컬럼과 값이 매핑된 딕셔너리입니다.
    - exception: 발생된 예외의 __cause__ 속성을 통해 QueryError 인스턴스를 가져올 수 있습니다.
        - 그리고 QueryError 객체의 sql 속성을 통해 실패한 SQL 객체를 가져올 수 있습니다.
    - _retry: 함수 내부적으로 재시도 로직에 사용되므로 외부에서 값을 주입하지 마세요.
    """

    async def _exec(_sql: SQL, cur):
        query, params = _sql.encode()
        try:
            await cur.execute(query, params)
            if _sql.fetch is False:
                return None
            rows = await cur.fetchall()
            if _sql.fetch == "all":
                return rows
            elif _sql.fetch == "one":
                return rows[0] if rows else None
        except Exception as e:
            # DB 에러에 따른 분기 처리를 위해서 psycopg의 예외 클래스를 raise 해야 함
            raise e from QueryError(_sql)  # e.__cause__ = QueryError(_sql)

    try:
        async with await psycopg.AsyncConnection.connect(
            host=SECRETS["DB_HOST"],
            dbname=dbname,
            user=SECRETS["DB_USERNAME"],
            password=SECRETS["DB_PASSWORD"],
            row_factory=dict_row,
        ) as conn:
            if _retry:
                log.info("[DB] Secrets Manager로부터 업데이트된 암호로 인증에 성공하였습니다.")
            async with conn.cursor() as cur:
                tasks = [_exec(_sql, cur) for _sql in sql]
                results = await asyncio.gather(*tasks)
                return {_sql: result for _sql, result in zip(sql, results)}
    except psycopg.OperationalError as e:
        if _retry:
            raise e
        # Secrets Manager에서 암호 교체가 이루어졌다고 간주하고 암호 업데이트 후 재시도
        SECRETS["DB_PASSWORD"] = json.loads(  # 최신 비밀번호로 업데이트
            boto3.client("secretsmanager").get_secret_value(
                SecretId=SECRETS["RDS_SECRET_MANAGER_ARN"]
            )["SecretString"]
        )["password"]
        log.info("[DB] 암호 변경 감지. Secrets Manager로부터 암호를 업데이트합니다.")
        return exec(*sql, dbname, _retry=True)  # 재시도


class SQL:
    def __init__(
        self,
        query: str,
        params: Dict[str, Any] = {},
        fetch: Literal[False, "one", "all"] = "one",
    ):
        """
        - PostgreSQL 문자열 컨벤션이 아닌 python 객체를 사용합니다. 문자열을 ''로 감싸지 마세요
        - 쿼리 마지막에 세미콜론 붙일 필요 없습니다.
        - params의 키는 숫자일 수 없습니다. 문자열만 허용됩니다.
        - fetch:
            - False: 쓰기 쿼리인 경우 -> None
            - "one": 하나의 레코드만 읽는 경우 -> Dict[str, Any]
                - 응답된 레코드가 하나도 없는 경우 -> None
            - "all": 여러 레코드를 읽는 경우 -> List[Dict[str, Any]]
                - 응답된 레코드가 하나도 없는 경우 -> []
        """
        if (query := query.strip()) and (query[-1] != ";"):
            query += ";"
        self.query = query
        self.params = params
        self.fetch = fetch
        # QueryError 쓰려면 우선 SQL 객체가 구성되어야 하므로 이 코드들은 밑에 있어야 함
        if query.upper()[:6] != "SELECT" and fetch is not False:
            error_msg = f"[SQL 객체 생성 불가] Write 쿼리는 fetch를 수행할 수 없습니다. ({query})"
            raise QueryError(self, error_msg)
        if fetch not in [False, "one", "all"]:
            error_msg = f"[SQL 객체 생성 불가] fetch 매개변수는 {fetch} 일 수 없습니다."
            raise QueryError(self, error_msg)

    def __repr__(self) -> str:
        repr_query = self.query.replace("\n", "  ")
        return f"<SQL (fetch={self.fetch}) {repr_query.format(**self.params)} >"

    def encode(self) -> Tuple[str, tuple]:
        # 쿼리에서 사용되는 파라미터 키들
        param_keys = re.findall(r"\{(.*?)\}", self.query)
        # 쿼리에 넣어줘야 하는 파라미터 값들
        param_values = tuple(self.params[key] for key in param_keys)
        # 쿼리의 {}를 %s로 변환
        query = re.sub(r"\{(.*?)\}", "%s", self.query)
        return query, param_values

    async def exec(self, dbname: str = "econox"):
        fetched = await exec(self, dbname=dbname)
        return fetched[self]


class InsertSQL(SQL):  # where 등 복잡한 구문이 없으므로 추상화 가능
    def __init__(self, table: str, **params):
        """
        - table: 데이터를 삽입할 테이블
            - [!] SQL 인젝션에 대한 보안을 위해서 table 매개변수는 반드시
                리터럴 값이어야 하며, 외부로부터 입력받아선 안됩니다.
        - params: 컬럼명, 값 쌍들
        """
        keys = tuple(params.keys())
        keys_str = f"({', '.join(keys)})"
        values_str = ", ".join([f"{{{key}}}" for key in keys])
        # 테이블 이름은 파라미터화 할 수 없습니다.
        query = f"INSERT INTO {table} {keys_str} VALUES ({values_str})"
        super().__init__(query, params, fetch=False)


# ======================== 단축 함수들 ========================


async def user_exists(email: str) -> bool:
    sql = SQL("SELECT id FROM users WHERE email={email}", params={"email": email})
    return bool(await sql.exec())


async def signup_history_exists(email: str, phone: str) -> bool:
    query = """
        SELECT id FROM signup_histories 
        WHERE email={email} or phone={phone}
        LIMIT 1
    """  # email, phone이 UNIQUE가 아니라서 LIMIT 1 해줘야 함
    sql = SQL(query, params={"email": email, "phone": phone})
    return bool(await sql.exec())


async def payment_method_exists(email: str) -> bool:
    """결제수단 등록 여부"""
    sql = SQL("SELECT * FROM users WHERE email={email}", {"email": email})
    if user := await sql.exec() is None:
        raise QueryError(sql, "[payment_method_exists]: 해당하는 유저가 없습니다!")
    return bool(
        (user["currency"] == "KRW" and user["tosspayments_billing_key"])
        or (user["currency"] == "USD" and user["paypal_subscription_id"])
    )
