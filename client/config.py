import os
import shutil
from pathlib import Path

ROOT_PATH = Path(__file__).parent.parent
DATA_PATH = ROOT_PATH / "efs-volume"
TIME_SERIES_PATH = DATA_PATH / "time-series"
LRU_CACHE_SIZE = 512  # lru_cache의 max_size

if DATA_PATH.exists():  # 첫 실행 시 디스크 데이터 초기화
    shutil.rmtree(DATA_PATH)
TIME_SERIES_PATH.mkdir(parents=True)

# GCP Credentials 설정: 해당 경로에 gcp_credential.json이 있어야 합니다.
if (gcp_credential_path := ROOT_PATH / "client/translate/gcp_credential.json").exists():
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(gcp_credential_path)
else:
    raise LookupError(f"{gcp_credential_path} 파일이 없어서 GCP 클라우드를 사용할 수 없습니다.")
