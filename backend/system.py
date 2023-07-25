import os
import json
import logging
import logging.config
from pathlib import Path
from datetime import datetime

import boto3


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
DATA_PATH = ROOT_PATH / "efs-volume"  # EFS volume mount path
XARRAY_PATH = DATA_PATH / "xarray"  # zarr array path for cache
INFO_PATH = DATA_PATH / "info"  # json path for cache

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
