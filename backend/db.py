"""
- exec 함수로 자유롭게 쿼리를 실행하세요
- 복잡한 쿼리는 Template 클래스를 통해 간결하게 생성하세요
- Transaction 클래스를 사용하면 단일 트렌젝션으로 여러개의 쿼리를 원하는 순서로 실행할 수 있습니다.
    - 여러 쿼리 실행은 exec 함수로도 가능하나, Template을 쓰는 경우 Transaction 클래스를 사용해야 합니다.
- 자주 사용되는 쿼리 로직은 간단한 함수로 만들어 사용하세요 (예시: user_exists, signup_history_exists)
"""

import re
import json
from typing import Tuple

import boto3
import psycopg

from backend.system import SECRETS, run_async, log

# ======== 쿼리 실행 함수 =========


async def exec(
    *queries: str, template: Tuple[str, dict] = None, embed=False, **params
) -> list | tuple:
    """
    - DB에 SQL 쿼리를 실행하고 결과를 반환합니다.
    - queries: 쿼리 템플릿 문자열
    - params: 템플릿 문자열에 할당해야 하는 매개변수
        - Python 객체를 받습니다. PostgreSQL 객체를 문자열로 표현하지 마세요
    - template: 쿼리 문자열과 파라미터 딕셔너리로 이루어진 튜플입니다.
        - queries, params 매개변수를 직접 넣지 않고 Template 클래스를 통해 쿼리를 생성하는 경우 사용합니다.
        - template 여러개를 단일 트렌젝션으로 실행하려면 Transaction 클래스를 사용하세요
    - embed: 결과중 첫번째 튜플을 반환합니다. 단일 행을 읽을때 True로 설정하세요
    - 사용 예
        - `db.exec("SELECT name={name} FROM {table};", table="user", name="John")`
        - 여러개의 쿼리 문자열도 허용됩니다. (너무 길어서 예시코드 안만듬)
    """
    if template:
        *queries, params = template
    query = " \n".join(queries)

    safe_queries, safe_params = [], []
    for query in queries:
        # psycopg의 Parameterized Queries 사용을 위해 { } -> %s
        safe_queries.append(re.sub(r"\{(.*?)\}", "%s", query))
        # 올바르게 정렬된 매개변수 배열
        safe_params.append([params[key] for key in re.findall(r"\{(.*?)\}", query)])

    def sync_exec():
        try:
            conn = psycopg.connect(
                host=SECRETS["DB_HOST"],
                dbname=SECRETS["DB_NAME"],
                user=SECRETS["DB_USERNAME"],
                password=SECRETS["DB_PASSWORD"],
            )
            cur = conn.cursor()
            for query, params in zip(safe_queries, safe_params):
                cur.execute(query, params)
            conn.commit()
            return cur.fetchall()
        except psycopg.ProgrammingError as e:
            # write 쿼리이기 때문에 읽을 결과가 없는 경우는 제외
            if str(e) != "the last operation didn't produce a result":
                raise e
        except psycopg.OperationalError as e:  # password authentication failed
            # Secrets Manager에서 암호 교체가 이루어졌다고 간주하고 암호 업데이트 후 재시도
            latest_password = json.loads(
                boto3.client("secretsmanager").get_secret_value(
                    SecretId=SECRETS["RDS_SECRET_MANAGER_ARN"]
                )["SecretString"]
            )["password"]
            SECRETS["DB_PASSWORD"] = latest_password
            log.warning(
                f"\n{e}\n DB 연결 오류가 발생하였습니다. Secrets Manager로부터 암호를 업데이트하여 재시도합니다."
            )
            return sync_exec()
        except Exception as e:
            conn.rollback()
            log.critical(f"\n{e}\nDB 쿼리 실행 오류가 발생하여 롤백하였습니다.\nQuery: {query}")
            raise e
        finally:
            cur.close()
            conn.close()

    result = await run_async(sync_exec)
    return result if not embed else (result[0] if result else tuple())


# ======== 쿼리 생성 함수 =========


class Template:
    """
    - 템플릿은 쿼리 문자열과 파라미터 딕셔너리로 이루어진 튜플입니다.
    - exec등의 메서드에서 query, params 매개변수 대신 template 매개변수를 통해 실행하면 됩니다.
    """

    def __init__(self, table: str):
        self.table = table

    def insert_query(self, **params) -> Tuple[str, dict]:
        columns = ", ".join(params.keys())
        values = ", ".join([f"{{{column}}}" for column in params.keys()])
        return f"INSERT INTO {self.table} ({columns}) VALUES ({values});", params

    def select_query(
        self, *columns: str, where: dict, limit: int | None = None
    ) -> Tuple[str, dict]:
        """
        - columns: 선택할 열 이름들
        - where: 조건을 구성할 딕셔너리
        - limit: LIMIT 인자
        """
        select = ", ".join(columns)
        cond = " AND ".join(f"{key}='{value}'" for key, value in where.items())
        end = f"LIMIT {limit};" if limit else ";"
        return f"SELECT {select} FROM {self.table} WHERE {cond} {end}", {}


# ======== 쿼리 실행 추상화 함수 =========


class Transaction:
    def __init__(self):
        """
        - 단일 트렌젝션으로 여러개의 쿼리를 실행합니다
        - prepend, append 메서드를 통해 쿼리 순서를 설정하세요
            - prepend(앞에 추가), append(뒤에추가)
        - set 메서드를 사용해서 한번에 여러개를 추가할 수 있습니다.
        """
        self.query_list = []
        self.param_dict = {}

    def prepend(self, query="", template=None, **params):
        if template:
            query, params = template
        self.query_list.insert(0, query)
        self.param_dict = params | self.param_dict

    def append(self, query="", template=None, **params):
        if template:
            query, params = template
        self.query_list.append(query)
        self.param_dict |= params

    async def exec(self):
        return await exec(*self.query_list, **self.param_dict)


async def user_exists(email: str) -> bool:
    query = "SELECT 1 FROM users WHERE email={email} LIMIT 1;"
    return bool(await exec(query, email=email))


async def signup_history_exists(email: str, phone: str) -> bool:
    query = """
        SELECT 1 FROM signup_histories 
        WHERE email={email} or phone={phone}
        LIMIT 1;
    """
    return bool(await exec(query, email=email, phone=phone))
