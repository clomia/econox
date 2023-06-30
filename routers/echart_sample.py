import numpy as np
from fastapi import Request, APIRouter
from fastapi.templating import Jinja2Templates

from client import fmp

router = APIRouter()
templates = Jinja2Templates(directory="templates/echart_sample")


@router.get("/echart")
def main_page(request: Request):
    return templates.TemplateResponse("main.jinja", {"request": request})


@router.get("/echart/data")
def main_page(request: Request, element: str, factor: str):
    print(request, element, factor)
    attr, fac = factor.split(".")
    symbol = fmp.Symbol(element)
    factor = getattr(getattr(symbol, attr), fac)
    data = factor().daily
    t = np.datetime_as_string(data.t.values, unit="D")
    return {"values": list(data.values), "t": list(t)}
