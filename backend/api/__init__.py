""" 
- API Routers 
- api 모듈 작성 방법
    - 모듈은 backend/api/ 디렉토리 안에 작성한다. 모듈명은 자유롭게 하되 API 첫번째 경로 인자로 하는걸 권장한다.
    - 모듈 안에 라우터를 선언한다.
        - 1. 단일 라우터 객체: APIRouter 인스턴스를 router 변수로 선언한다.
        - 2. 여러개의 라우터 객체: APIRouter 인스턴스로 이루어진 리스트를 router 변수로 선언한다.
    - 선언한 라우터를 API 함수에 데코레이터로 사용한다.
"""
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
