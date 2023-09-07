""" API Routers """
from pathlib import Path
from importlib import import_module

from backend.api import *

routers = []  # 사용되는 모든 API 라우터들.
for p in Path(__file__).parent.glob("*.py"):
    if p.name == "__init__.py":
        continue
    module = import_module(f"backend.api.{p.stem}")
    routers.append(module.router.public)
    routers.append(module.router.private)
