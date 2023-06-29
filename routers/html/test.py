from functools import partial

from fastapi import Request, APIRouter

from compute import parallel
from system import templates
from client import fmp, world_bank

router = APIRouter()


@router.get("/")
def main_page(request: Request):
    return templates.TemplateResponse("main.jinja", {"request": request})


@router.get("/result")
async def result_page(request: Request, text: str):
    results = await parallel.async_executor(
        fmp_search := partial(fmp.search, text),
        world_bank_search := partial(world_bank.search, text),
    )
    return templates.TemplateResponse(
        "result.jinja",
        {
            "request": request,
            "symbols": results[fmp_search],
            "countries": results[world_bank_search],
        },
    )
