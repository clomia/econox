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


class QueryError(Exception):
    def __init__(self, sql: SQL, msg: str = ""):
        self.sql = sql
        super().__init__(f"[DB Error] {sql} {msg}")


async def exec(
    *sql: SQL,
    dbname: str = "main",
    parallel: bool = False,
    _retry=0,
) -> Dict[SQL, None | List[Dict[str, Any]]]:
    """
    - 여러 SQL을 동시에 실행합니다. 하나의 트렌젝션으로 취급되며 하나라도 실패하면 모두 안전하게 롤백됩니다.
    - parallel: 병렬 처리 활성화 여부
        - 여러 SQL을 실행할 때, 각각의 SQL이 서로 종속성을 띄지 않는 경우 병렬 옵션을 활성화 하세요.
        - 종속성을 띄는 SQL들을 병렬로 수행하지 마세요!
    - retuen: SQL에 대한 결과가 딕셔너리로 매핑되어 반환됩니다.
        - 그리고 결과는 컬럼과 값이 매핑된 딕셔너리입니다.
    - exception: 발생된 예외의 __cause__ 속성을 통해 QueryError 인스턴스를 가져올 수 있습니다.
        - 그리고 QueryError 객체의 sql 속성을 통해 실패한 SQL 객체를 가져올 수 있습니다.
    - _retry: 함수 내부적으로 재시도 로직에 사용되므로 외부에서 값을 주입하지 마세요.
    """

    async def _exec(_sql: SQL, cur):
        try:
            query, params = _sql.encode()
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
            if _retry > 0:
                log.info("[DB] Secrets Manager로부터 업데이트된 암호로 인증에 성공하였습니다.")
            async with conn.cursor() as cur:
                tasks = [_exec(_sql, cur) for _sql in sql]
                if parallel:
                    results = await asyncio.gather(*tasks)  # 동시 실행
                else:
                    results = [await task for task in tasks]  # 순차 실행
                return {_sql: result for _sql, result in zip(sql, results)}
    except psycopg.OperationalError as e:
        if _retry > 50:
            log.critical(f"{e} 에러로 인해 50회 재시도하였으나 실패하였습니다!")
            raise e
        log.info(
            "[DB] 암호 변경 감지. Secrets Manager로부터 암호를 업데이트합니다.\n"
            f"현재까지 {_retry}번 재시도되었습니다. DB 암호 업데이트는 적용까지 약 1분 소요됩니다."
        )
        secret_manager = boto3.client("secretsmanager")
        try:
            # Secrets Manager에서 암호 교체가 이루어졌다고 간주하고 암호 업데이트
            SECRETS["DB_PASSWORD"] = json.loads(  # 최신 비밀번호로 업데이트
                secret_manager.get_secret_value(
                    SecretId=SECRETS["RDS_SECRET_MANAGER_ARN"]
                )["SecretString"]
            )["password"]
        except secret_manager.exceptions.EndpointConnectionError as e:
            # AWS에서 암호 교체가 이루어지는 중에는 일시적으로 SecretManager 접속이 안된다.
            log.warn(
                f"[DB] Secrets Manager가 응답하지 않습니다: {e.__class__.__name__} ({e})\n"
                "AWS RDS Aurora의 DB 암호 교체가 시작되면 일시적으로 Secret Manager 접속이 안될 수 있습니다."
            )
        return await exec(*sql, dbname=dbname, _retry=_retry + 1)  # 재시도


class SQL:
    def __init__(
        self,
        query: str,
        params: Dict[str, Any] = {},
        fetch: Literal[False, "one", "all"] = False,
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
        _q = query.upper()
        if not (_q[:6] == "SELECT" or "RETURNING" in _q) and fetch is not False:
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

    async def exec(self, dbname: str = "main"):
        fetched = await exec(self, dbname=dbname)
        return fetched[self]


class InsertSQL(SQL):
    def __init__(self, table: str, returning: bool = False, **params):
        """
        - table: 데이터를 삽입할 테이블
        - returning: 실행 시 삽입에 성공한 레코드가 모두 반환됩니다.
        - params: 컬럼명, 값 쌍들
        """
        keys = tuple(params.keys())
        keys_str = f"({', '.join(keys)})"
        values_str = ", ".join([f"{{{key}}}" for key in keys])
        # 테이블 이름은 파라미터화 할 수 없습니다.
        query = f"INSERT INTO {table} {keys_str} VALUES ({values_str})"
        if returning:
            query += " RETURNING *"
        super().__init__(query, params, fetch="one" if returning else False)


class ManyInsertSQL(SQL):
    def __init__(
        self,
        table: str,
        params: Dict[str, list],
        conflict_pass: list = [],
        returning: bool = False,
    ):
        """
        - table: 데이터를 삽입할 테이블
        - params: 컬럼명, 값 리스트
            - 모든 리스트의 길이는 동일해야 합니다.
        - conflict_pass: 제약 조건에 대해 에러 출력 없이 넘어갈 컬럼 지정
        - returning: 실행 시 삽입에 성공한 레코드가 모두 반환됩니다.
        """
        list_lengths = [len(lst) for lst in params.values()]
        if not all(length == list_lengths[0] for length in list_lengths):
            raise ValueError(f"[ManyInsertSQL] params 값 리스트의 길이가 동일하지 않습니다")
        keys = tuple(params.keys())
        length = len(params[keys[0]])

        keys_str = f"({', '.join(keys)})"
        values_str = ", ".join(
            [
                f'({", ".join([f"{{{idx}_{key}}}" for key in keys])})'
                for idx in range(length)
            ]
        )

        params_dict = {}
        for key in keys:
            for idx, value in enumerate(params[key]):
                params_dict[f"{idx}_{key}"] = value

        query = f"INSERT INTO {table} {keys_str} VALUES {values_str}"

        if conflict_pass:
            query += f" ON CONFLICT ({', '.join(conflict_pass)}) DO NOTHING"
        if returning:
            query += " RETURNING *"

        super().__init__(query, params_dict, fetch="all" if returning else False)


# ======================== 단축 함수들 ========================


async def get_user(*, email: str = None, user_id: str = None) -> dict | None:
    """
    - 유저 레코드 가져오기
    - email, user_id 둘 중 하나만 입력하세요.
    - 해당하는 유저가 없으면 None을 반환합니다.
    """
    if email is not None:
        sql = SQL(
            "SELECT * FROM users WHERE email={email}",
            params={"email": email},
            fetch="one",
        )
    elif user_id is not None:
        sql = SQL(
            "SELECT * FROM users WHERE id={id}", params={"id": user_id}, fetch="one"
        )
    else:
        raise TypeError(f"[db.get_user] 매개변수가 입력되지 않았습니다.")
    return await sql.exec()


async def signup_history_exists(email: str, phone: str) -> bool:
    query = """
        SELECT id FROM signup_histories 
        WHERE email={email} or phone={phone}
        LIMIT 1
    """  # email, phone이 UNIQUE가 아니라서 LIMIT 1 해줘야 함
    sql = SQL(query, params={"email": email, "phone": phone}, fetch="one")
    return bool(await sql.exec())
