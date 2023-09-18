""" API Routers """
from pathlib import Path
from importlib import import_module

from backend.api import *
from backend.http import APIRouter

routers = []  # 사용되는 모든 API 라우터들.
for p in Path(__file__).parent.glob("*.py"):
    if p.name == "__init__.py":
        continue
    module = import_module(f"backend.api.{p.stem}")
    if hasattr(module, "router"):
        if isinstance(module.router, (list, tuple)):
            for router in module.router:
                routers.append(router.public)
                routers.append(router.private)
        elif isinstance(module.router, APIRouter):
            routers.append(module.router.public)
            routers.append(module.router.private)
