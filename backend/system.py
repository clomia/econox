""" 백엔드 전반에 필요한 인프라, 모니터링, 최적화 모듈"""

import os
import json
import asyncio
import logging
import logging.config
from pathlib import Path
from datetime import datetime
from functools import partial
from typing import Callable, Any, Dict
from concurrent.futures import ThreadPoolExecutor

import boto3
import psycopg


# ==================== logger object ====================
class LogHandler(logging.NullHandler):
    pid = os.getpid()

    def __init__(self):
        super().__init__()

    def handle(self, record):
        now = datetime.now()
        time = f"{now.month}/{now.day} {now.hour}시 {now.minute}분 {now.second}초"
        content = f"[{record.levelname}][{time}][pid:{self.pid}] {self.format(record)}"
        print(content)


log = logging.getLogger("app")
log.propagate = False  # FastAPI나 Uvicorn 등 다른 로깅 출력에 전파되지 않도록
log.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(message)s")
log_handler = LogHandler()
log_handler.setFormatter(formatter)
log_handler.setLevel(logging.DEBUG)
log.addHandler(log_handler)

# ==================== CONSTANTS ====================
ROOT_PATH = Path(__file__).parent.parent
EFS_VOLUME_PATH = ROOT_PATH / "efs-volume"

S3_BUCKET_NAME = "econox-storage"
SECRET_MANAGER_NAME = "econox-secret"
# ==================== SECRETS ====================
# Secret manager에 정의된 보안 데이터를 딕셔너리로 정리합니다.
secret_manager = boto3.client("secretsmanager")
data = secret_manager.get_secret_value(SecretId=SECRET_MANAGER_NAME)
secrets = json.loads(data["SecretString"])
# DB 비밀번호는 Aurora가 직접 관리하는 다른 secretsmanager에 있음
db_data = secret_manager.get_secret_value(SecretId=secrets["RDS_SECRET_MANAGER_ARN"])
db_secrets = json.loads(db_data["SecretString"])

SECRETS = dict(secrets)
SECRETS["DB_PASSWORD"] = db_secrets["password"]

log.debug(
    f"보안 데이터 {len(SECRETS)}개 로드 완료\n"
    f"---------- 로드된 보안 데이터 목록 ----------\n"
    f"{list(SECRETS.keys())}\n"
    "----------------------------------------------\n"
)


# ==================== FUNCTIONS ====================
async def run_async_parallel(*functions) -> Dict[Callable[[], Any], Any]:
    """
    - 여러개의 동기 함수를 병렬로 실행하는 비동기 함수입니다.
    - 비동기 함수 병렬 실행은 Parallel 말고 asyncio.gather를 사용하세요
    - I/O-bound 최적화에 유효한 병렬화만 가능합니다.
        - 서버 자체가 이미 모든 CPU 코어를 사용하기 때문에 멀티 프로세싱은 하면 안됌
    - `results = await async_parallel(func1, func2, func3, ...)`
    - `func1_returned = results[func1]`
    """
    if not functions:
        return {}
    with ThreadPoolExecutor(max_workers=len(functions)) as executor:
        loop = asyncio.get_running_loop()
        futures = [loop.run_in_executor(executor, func) for func in functions]
        results = await asyncio.gather(*futures)
    return dict(zip(functions, results))


async def run_async(func, *args, **kwargs):
    """단일 동기 함수를 비동기로 실행합니다."""
    target = partial(func, *args, **kwargs)
    return (await run_async_parallel(target))[target]


async def db_exec_query(query: str) -> list:
    """RDS Database에 SQL 쿼리를 실행하고 결과를 반환합니다."""

    def execute_query():
        try:
            conn = psycopg.connect(
                host=SECRETS["DB_HOST"],
                dbname=SECRETS["DB_NAME"],
                user=SECRETS["DB_USERNAME"],
                password=SECRETS["DB_PASSWORD"],
            )
            cur = conn.cursor()
            cur.execute(query)
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
                f"[{e}] DB 연결 오류가 발생하였습니다. Secrets Manager로부터 암호를 업데이트하여 재시도합니다."
            )
            return db_exec_query(query)
        except Exception as e:
            conn.rollback()
            log.critical(f"[{e}] DB 쿼리 실행 오류가 발생하여 롤백하였습니다.\nQuery: {query}")
            raise e
        finally:
            cur.close()
            conn.close()

    return await run_async(execute_query)
