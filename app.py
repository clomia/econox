""" FastAPI로 ASGI app 객체 생성 """
from functools import partial

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from client import fmp, world_bank
from compute.parallel import AsyncExecutor

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"))
templates = Jinja2Templates(directory="templates")


@app.get("/")
def main_page(request: Request):
    return templates.TemplateResponse("main.jinja", {"request": request})


@app.get("/search")
def main_page(request: Request, text: str):
    results = AsyncExecutor(
        fmp_search := partial(fmp.search, text),
        world_bank_search := partial(world_bank.search, text),
    ).execute()
    return templates.TemplateResponse(
        "result.jinja",
        {
            "request": request,
            "symbols": results[fmp_search],
            "countries": results[world_bank_search],
        },
    )
