import time
from pathlib import Path

import xarray as xr


def xr_open_zarr(path: Path, timeout=5):
    """
    - EFS 사용에 따른 동시성 취약 문제를 핸들링해줍니다.
    - 현재까지 발견된 문제들
        - EFS에 .zarr 폴더가 있고, 내부 데이터가 완성되기 전에 읽으면 FileNotFoundError가 발생한다.
            네트워크 속도 문제도 있겠지만, .zarr 폴더 자체가 없다는 에러도 발생했기 때문에 복잡한 안정성 문제로 취급.
    """
    start = time.time()
    while time.time() - start < timeout:
        try:
            return xr.open_zarr(path)
        except:
            pass
    return xr.open_zarr(path)  # timeout동안 계속 시도했음에도 에러가 반복되는 상황이다.
