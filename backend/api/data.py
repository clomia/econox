import numpy as np

from backend.client import fmp
from backend.api import router


@router.get("/data/time-series/symbol/adj-close")
def adj_close(element: str):
    print(f"요청 수신! {element}")
    symbol = fmp.Symbol(element)
    daily = symbol.price.adj_close().daily
    return {
        "name": symbol.name.ko,
        "note": symbol.note.ko,
        "values": daily.values.tolist(),
        "t": np.datetime_as_string(daily.t.values, unit="D").tolist(),
    }
