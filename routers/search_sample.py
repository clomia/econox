from functools import partial

from fastapi import Request, APIRouter
from fastapi.templating import Jinja2Templates

from compute import parallel
from client import fmp, world_bank

router = APIRouter()
templates = Jinja2Templates(directory="templates/search_sample")


@router.get("/search")
def main_page(request: Request):
    return templates.TemplateResponse("main.jinja", {"request": request})


def get_name_ko(objects):
    results = parallel.executor(
        *[partial(lambda obj: obj.name.ko, obj) for obj in objects]
    )
    return list(results.values())


def get_note_ko(objects):
    results = parallel.executor(
        *[partial(lambda obj: obj.note.ko, obj) for obj in objects]
    )
    return list(results.values())


@router.get("/search/result")
async def result_page(request: Request, text: str):
    results = await parallel.async_executor(
        fmp_search := partial(fmp.search, text),
        world_bank_search := partial(world_bank.search, text),
    )
    symbols = results[fmp_search]
    countries = results[world_bank_search]
    results = await parallel.async_executor(
        symbol_names := partial(get_name_ko, symbols),
        country_names := partial(get_name_ko, countries),
        symbol_notes := partial(get_note_ko, symbols),
        country_notes := partial(get_note_ko, countries),
    )
    return templates.TemplateResponse(
        "result.jinja",
        {
            "request": request,
            "symbols": zip(results[symbol_names], results[symbol_notes]),
            "countries": zip(results[country_names], results[country_notes]),
        },
    )
