""" FastAPI로 ASGI app 객체 생성 """
from functools import partial

from fastapi import FastAPI, Request
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from client import fmp, world_bank
from compute import parallel
from system import log

app = FastAPI()


app.mount("/static", StaticFiles(directory="static"))
templates = Jinja2Templates(directory="templates")


@app.get("/")
async def main_page(request: Request):
    return templates.TemplateResponse("main.jinja", {"request": request})


@app.get("/result")
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
