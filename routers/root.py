from fastapi import Request, APIRouter

router = APIRouter()


@router.get("/")
def main_page(request: Request):
    return "개발중입니다..."
