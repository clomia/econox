import numpy as np
from fastapi import APIRouter

from backend.client import fmp

router = APIRouter()


@router.get("/time-series/symbol/adj-close")
def adj_close(elements: str):
    symbol = fmp.Symbol(elements)
    daily = symbol.price.adj_close().daily
    return {
        "name": symbol.name.ko,
        "note": symbol.note.ko,
        "values": daily.values.tolist(),
        "t": np.datetime_as_string(daily.t.values, unit="D").tolist(),
    }
