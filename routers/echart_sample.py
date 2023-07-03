import numpy as np
from fastapi import Request, APIRouter
from fastapi.templating import Jinja2Templates

from client import fmp

router = APIRouter()
templates = Jinja2Templates(directory="templates/echart_sample")


@router.get("/echart")
def main_page(request: Request):
    return templates.TemplateResponse("main.jinja", {"request": request})


def symbol2dict(symbol):
    print(symbol)
    data = symbol.price.adj_close().daily.isel(t=slice(-1000, None))
    return {
        "name": symbol.name.ko,
        "values": list(data.values),
        "t": list(np.datetime_as_string(data.t.values, unit="D")),
    }


@router.get("/echart/data")
def main_page(request: Request, elements: str):
    return [symbol2dict(fmp.Symbol(code)) for code in elements.split(",")]
