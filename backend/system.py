""" 백엔드 전반에 필요한 인프라, 모니터링, 최적화 모듈"""

import os
import json
import uuid
import asyncio
import logging
import logging.config
from pathlib import Path
from datetime import datetime
from functools import partial, wraps
from typing import Callable, Any, Dict
from concurrent.futures import ThreadPoolExecutor

import psutil
import boto3
import aiocache
import redis.asyncio as redis


# ==================== LOGGING ====================
class LogHandler(logging.NullHandler):
    pid = os.getpid()

    def __init__(self):
        super().__init__()

    def handle(self, record):
        now = datetime.now()
        memory = psutil.virtual_memory()
        memory_used = memory.total - memory.available
        memory_percent = (memory_used / memory.total) * 100

        disk = psutil.disk_usage("/")
        disk_used = disk.total - disk.free
        disk_percent = (disk_used / disk.total) * 100

        memory_percent = f"{memory_percent:.0f}%"
        disk_percent = f"{disk_percent:.0f}%"
        memory_gb = f"{memory_used * 1e-9:.0f}GB"
        disk_gb = f"{disk_used * 1e-9:.0f}GB"

        memory_status = f"메모리: {memory_gb}({memory_percent})"
        disk_status = f"디스크: {disk_gb}({disk_percent})"
        time = f"{now.month}/{now.day} {now.hour}시 {now.minute}분 {now.second}초"
        content = f"[{record.levelname}][{time}][pid:{self.pid}][{disk_status}][{memory_status}]: {self.format(record)}"
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
# ==================== SETTINGS ====================
MEMBERSHIP = {
    "basic": {
        "KRW": 11900,
        "USD": 9.99,
        "paypal_plan": "P-32P35738U4826650TMT72TNA",
    },
    "professional": {
        "KRW": 15900,
        "USD": 12.99,
        "paypal_plan": "P-8U118819R1222424SMT72UDI",
    },
}
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

is_local = bool(os.getenv("IS_LOCAL"))
if is_local:
    SECRETS["RADIS_HOST"] = "localhost"


# 일반 커넥션 풀은 최대 연결 초과시 예외를 반환하지만 BlockingConnectionPool은 기다리면서 진입각을 본다.
redis_connection_pool = redis.BlockingConnectionPool(
    # AWS ElastiCache는 SSL이 필수다. 로컬에서는 SSL 쓸 수 없다.
    connection_class=redis.SSLConnection if not is_local else redis.Connection,
    # 로컬, AWS ElastiCache 각각 Redis 서버가 감당 가능한 커넥션 역치가 있다.
    max_connections=200 if is_local else 500,
    host=SECRETS["RADIS_HOST"],
    timeout=30,
)  # * Redis 관련해서 timeout, 커넥션오류 등이 뜨면 max_connections을 줄여라
# socket_timeout, socket_connect_timeout는 None으로 하고 Uvicorn의 Timeout기능에 의존한다.
# 도저히 적정값을 모르겠으며, 이 설정을 주면 될것도 안되는 경우가 많이 발생한다.

REDIS_CONFIG = {  # 사용법: redis.Redis(**REDIS_CONFIG)
    "connection_pool": redis_connection_pool,
    "decode_responses": True,
}

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


class Idempotent:
    """
    - FastAPI 함수에 멱등성을 부여합니다. (동시에 실행되지 않도록 합니다.)
        - 비동기 함수라면 모두 사용 가능합니다.
    - EFS 파일 시스템에 함수의 실행 상태를 저장합니다.
        해당 함수가 이미 실행중인 경우 함수를 실행하지 않고 default를 반환합니다.

    ```python
    @router.public.get("/billing")
    @Idempotent(default={"message": "There are processors that already do this"})
    async def billing():
        ...
    ```
    """

    path = EFS_VOLUME_PATH / "idempotent"

    def __init__(self, default):
        """
        - default: 해당 함수가 이미 실행중인 경우,
            함수를 실행하지 않고 반환할 기본값
        """
        self.default = default

    def __call__(self, func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            mark = self.path / f"{func.__name__ }-{uuid.uuid4().hex[:10]}.txt"
            mark.parent.mkdir(parents=True, exist_ok=True)
            if mark.exists():  # 이미 실행중인 경우
                return self.default
            else:  # 아니라면 EFS에 마크 작성
                mark.write_text(f"{func.__module__}.{func.__name__}")
            try:
                return await func(*args, **kwargs)
            finally:
                mark.unlink()  # EFS에서 마크 제거

        return wrapper


class ElasticRedisCache(aiocache.RedisCache):
    """
    - AWS ElastiCache와의 호환성이 구현된 aiocache의 RedisCache 자식 클래스
    - 사용법 @cached(cache=ElasticRedisCache , ...)
    - aiocache에서 제공하는 Redis 백엔드 클래스는 ssl 매개변수를 설정할 수 없다.
        ssl 매개변수를 설정할 수 있어야 ElastiCache를 사용할 수 있으므로 상속을 통해 해결
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, timeout=None, **kwargs)
        self.client = redis.Redis(**REDIS_CONFIG | {"decode_responses": False})
