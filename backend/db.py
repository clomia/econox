"""
- exec 함수로 자유롭게 쿼리를 실행하세요
- 복잡한 쿼리는 Template 클래스를 통해 간결하게 생성하세요
- Transaction 클래스를 사용하면 단일 트렌젝션으로 여러개의 쿼리를 원하는 순서로 실행할 수 있습니다.
    - 여러 쿼리 실행은 exec 함수로도 가능하나, Template을 쓰는 경우 Transaction 클래스를 사용해야 합니다.
- 자주 사용되는 쿼리 로직은 간단한 함수로 만들어 사용하세요 (예시: user_exists, signup_history_exists)
- 쿼리 작성 시 세미콜론은 작성하지 않는걸 기본 컨벤션으로 합니다, 세미콜론 처리는 이 모듈에 맡기세요
    - [주의!] 단, db.exec에 문자열로 여러 쿼리를 넣는 경우는 세미콜론을 넣어줘야 합니다. 
"""

import re
import json
import asyncio
from typing import List, Tuple, Dict, Any

import boto3
import psycopg
from psycopg.rows import dict_row

from backend.system import SECRETS, log

# ======== 쿼리 실행 함수 =========


class SQL:
    def __init__(self, query: str, params: Dict[str, Any] = {}, fetch: bool = True):
        """PostgreSQL 문자열 컨벤션이 아닌 python 객체를 사용합니다. 문자열을 ''로 감싸지 마세요"""
        if "SELECT" not in query.upper() and fetch is True:
            raise Exception(f"[SQL 객체 생성 불가] Write 쿼리는 fetch를 수행할 수 없습니다. ({query})")
        self.query = query
        self.params = params
        self.fetch = fetch

    def __repr__(self) -> str:
        return f"<SQL (fetch={self.fetch}) {self.query} >"

    def encode(self) -> Tuple[str, tuple]:
        # 쿼리에서 사용되는 파라미터 키들
        param_keys = re.findall(r"\{(.*?)\}", self.query)
        # 쿼리에 넣어줘야 하는 파라미터 값들
        param_values = tuple(self.params[key] for key in param_keys)
        # 쿼리의 {}를 %s로 변환
        query_converted = re.sub(r"\{(.*?)\}", "%s", self.query)
        return query_converted, param_values


class QueryError(Exception):
    def __init__(self, sql: SQL):
        self.sql = sql
        super().__init__(f"SQL 실행 실패: {sql}")


async def exec(
    *sql: SQL,
    dbname: str = "econox",
    _retry=False,
) -> Dict[SQL, None | List[Dict[str, Any]]]:
    """
    - psycopg3의 비동기 클라이언트를 사용해서 여러 쿼리를 동시에 실행합니다.
        - 너무 많은 쿼리를 동시에 실행하면 DB 응답이 늦을 수 있습니다.
        - 실제로 쿼리의 병렬 처리 능력은 AWS RDS 클러스터의 인스턴스 갯수에 따라 다릅니다.
    - retuen: SQL에 대한 결과가 딕셔너리로 매핑되어 반환됩니다.
        - 그리고 결과는 컬럼과 값이 매핑된 딕셔너리입니다.
    - exception: 발생된 예외의 __cause__ 속성을 통해 QueryError 인스턴스를 가져올 수 있습니다.
        - 그리고 QueryError 객체의 sql 속성을 통해 실패한 SQL 객체를 가져올 수 있습니다.
    """

    async def execute_query(_sql: SQL, cur):
        query, params = _sql.encode()
        try:
            await cur.execute(query, params)
            return await cur.fetchall() if _sql.fetch else None
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
                tasks = [execute_query(_sql, cur) for _sql in sql]
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


class Transaction:
    def __init__(self, dbname: str = "econox"):
        """
        - 단일 트렌젝션으로 여러개의 쿼리를 실행합니다
        - prepend, append 메서드를 통해 쿼리 순서를 설정하세요
            - prepend(앞에 추가), append(뒤에추가)
        - set 메서드를 사용해서 한번에 여러개를 추가할 수 있습니다.
        """
        self.dbname = dbname
        self.query_list = []
        self.param_dict = {}

    def prepend(self, query: str, params):
        if (query := query.strip()) and (query[-1] != ";"):
            query += ";"  # 여러 쿼리 넣을땐 ; 로 구분해줘야 함
        self.query_list.insert(0, query)
        self.param_dict = params | self.param_dict

    def append(self, query: str, **params):
        if (query := query.strip()) and (query[-1] != ";"):
            query += ";"
        self.query_list.append(query)
        self.param_dict |= params

    async def exec(self):  # 하나의 SQL 객체로 만들어서 exec 해야 함!
        query = SQL(" ".join(self.query_list), params=self.param_dict)
        return await exec(query, dbname=self.dbname)


async def select_row(table: str, fields: list, where: dict):
    """
    - limit 1 로 하나의 레코드만 선택하여 dict 형태로 반환합니다.
    - 레코드가 없으면 빈 딕셔너리 반환
    """
    values = await exec(
        template=Template(table=table).select_query(*fields, where=where, limit=1),
        embed=True,
    )
    return {k: v for k, v in zip(fields, values)}


async def user_exists(email: str) -> bool:
    query = "SELECT 1 FROM users WHERE email={email};"
    return bool(await exec(query, params={"email": email}))


async def signup_history_exists(email: str, phone: str) -> bool:
    query = """
        SELECT 1 FROM signup_histories 
        WHERE email={email} or phone={phone}
        LIMIT 1;
    """
    return bool(await exec(query, params={"email": email, "phone": phone}))


async def payment_method_exists(email: str) -> bool:
    """결제수단 등록 여부"""
    db_user = await select_row(
        "users",
        fields=["currency", "tosspayments_billing_key", "paypal_subscription_id"],
        where={"email": email},
    )
    return bool(
        (db_user["currency"] == "KRW" and db_user["tosspayments_billing_key"])
        or (db_user["currency"] == "USD" and db_user["paypal_subscription_id"])
    )
