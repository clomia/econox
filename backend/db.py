import re
import json
from typing import Tuple

import boto3
import psycopg

from backend.system import SECRETS, run_async, log

# ======== 쿼리 실행 함수 =========


async def exec(*queries: str, **params) -> list:
    """
    - DB에 SQL 쿼리를 실행하고 결과를 반환합니다.
    - queries: 쿼리 템플릿 문자열
    - params: 템플릿 문자열에 할당해야 하는 매개변수
        - Python 객체를 받습니다. PostgreSQL 객체를 문자열로 표현하지 마세요
    - 사용 예
        - `db.exec("INSERT INTO {table} {name}", table="user", name="John")`
        - 여러개의 쿼리 문자열도 허용됩니다. (너무 길어서 예시코드 안만듬)
    """

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
            return cur.fetchall()  # case: read success
        except psycopg.ProgrammingError as e:
            return []  # case: write success
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

    return await run_async(sync_exec)


# ======== 쿼리 생성 함수 =========


def insert_query_template(table, **params) -> Tuple[str, tuple]:
    """exec 함수에 바로 넣을 수 있는 형태로 만들어 반환합니다."""
    columns = ", ".join(params.keys())
    values = ", ".join([f"{{{column}}}" for column in params.keys()])
    return f"INSERT INTO {table} ({columns}) VALUES ({values});", params


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

    def prepend(self, query, **params):
        self.query_list.insert(0, query)
        self.param_dict = params | self.param_dict

    def append(self, query, **params):
        self.query_list.append(query)
        self.param_dict |= params

    def prepend_template(self, template):
        query, params = template
        self.prepend(query, **params)

    def append_template(self, template):
        query, params = template
        self.append(query, **params)

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
