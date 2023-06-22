from pathlib import Path

ROOT_PATH = Path(__file__).parent
DATA_PATH = ROOT_PATH / "efs-volume"
XARRAY_PATH = DATA_PATH / "xarray"

LRU_CACHE_SIZE = 512  # lru_cache의 max_size

SYSTEM_S3_BUCKET_NAME = "econox-system"
GCP_CREDENTIAL_FILENAME = "gcp_credential.json"  # 시스템 버킷 안에 있어야 함

STORAGE_S3_BUCKET_NAME = "econox-storage"
