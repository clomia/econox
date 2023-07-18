from fastapi import APIRouter

router = APIRouter(prefix="/api")

# 모듈 실행을 통해 라우터에 함수 마운트
from backend.api import account, data
