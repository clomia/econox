import time
from pathlib import Path
from typing import Callable
from functools import partial

import xarray as xr

EFS_TIMEOUT = 8


def _pooling(callable: Callable):
    start = time.time()
    while time.time() - start < EFS_TIMEOUT:
        try:
            return callable()
        except:
            pass
    return callable()  # timeout동안 계속 시도했음에도 에러가 반복되는 상황이다.


def xr_open_zarr(path: Path):
    """
    - xarray의 open_zarr에 대한 wrapper
    - EFS 사용에 따른 동시성 취약 문제를 핸들링해줍니다.
    - 현재까지 발견된 문제들
        - EFS에 .zarr 폴더가 있고, 내부 데이터가 완성되기 전에 읽으면 FileNotFoundError가 발생한다.
            네트워크 속도 문제도 있겠지만, .zarr 폴더 자체가 없다는 에러도 발생했기 때문에 복잡한 안정성 문제로 취급.
        - 아래와 같은 경고 메세지가 뜨고, 메타데이터가 불러와지지 않는 에러 있음
            /server/backend/data/io.py:15: RuntimeWarning: Failed to open Zarr store with consolidated metadata, but successfully read with non-consolidated metadata. This is typically much slower for opening a dataset. To silence this warning, consider:
            1. Consolidating metadata in this existing store with zarr.consolidate_metadata().
            2. Explicitly setting consolidated=False, to avoid trying to read consolidate metadata, or
            3. Explicitly setting consolidated=True, to raise an error in this case instead of falling back to try reading non-consolidated metadata.
    """

    def proxy():
        data = xr.open_zarr(path)
        # 메타데이터 잘 불러와졌는지 체크
        assert data.attrs.get("client", {}).get("collected")
        return data

    return _pooling(proxy)


def xr_to_zarr(dataset: xr.Dataset, path: Path):
    """
    - xarray의 to_zarr에 대한 wrapper
    - EFS 사용에 따른 동시성 취약 문제를 핸들링해줍니다.
    - 현재까지 발견된 문제들
        - 동시접속으로 인한 PermissionError, 그리고 결과적으로 전파되는 FileNotFoundError등
    """
    return _pooling(partial(dataset.to_zarr, path, mode="w"))
