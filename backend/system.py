import logging
import logging.config
from pathlib import Path
from datetime import datetime

# ==================== CONSTANTS ====================

ROOT_PATH = Path(__file__).parent.parent
DATA_PATH = ROOT_PATH / "efs-volume"  # EFS volume mount path
XARRAY_PATH = DATA_PATH / "xarray"  # zarr array path for cache
INFO_PATH = DATA_PATH / "info"  # json path for cache

LRU_CACHE_SIZE = 1024  # lru_cache의 max_size

SYSTEM_S3_BUCKET_NAME = "econox-system"  # 환경변수파일, gcp_credential.json이 저장된 버킷
GCP_CREDENTIAL_FILENAME = "gcp_credential.json"  # 시스템 버킷 안에 있어야 함

STORAGE_S3_BUCKET_NAME = "econox-storage"  # 서버 운영에 사용되는 버킷

COGNITO_USER_POOL = "us-east-1_4FfzJH2Zw"  # user pool id

# ==================== logger object ====================


class LogHandler(logging.NullHandler):
    def __init__(self):
        super().__init__()

    def handle(self, record):
        now = datetime.now()
        time = f"{now.month}/{now.day} {now.hour}시 {now.minute}분 {now.second}초"
        content = f"[{record.levelname}][{time}] {self.format(record)}"
        print(content)


log = logging.getLogger("app")
log.propagate = False  # FastAPI나 Uvicorn 등 다른 로깅 출력에 전파되지 않도록
log.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(message)s")
log_handler = LogHandler()
log_handler.setFormatter(formatter)
log_handler.setLevel(logging.DEBUG)
log.addHandler(log_handler)
