from pathlib import Path
from importlib import import_module

from fastapi import APIRouter

router = APIRouter(prefix="/api")

# 모든 api 함수들을 router에 붙입니다.
for p in Path(__file__).parent.glob("*.py"):
    if p.name == "__init__.py":
        continue
    import_module(f"backend.api.{p.stem}")
