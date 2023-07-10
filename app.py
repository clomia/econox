""" FastAPI로 ASGI app 객체 생성 """
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend import api

app = FastAPI()

# ================= backend =================
app.include_router(api.data.router, prefix="/api/data")


# ================= frontend =================
app.mount("/static", StaticFiles(directory="frontend/static"))


@app.get("/{page:path}")  # SPA Svelte APP hosting
def frontend() -> HTMLResponse:
    html = Path("frontend/static/index.html").read_text()
    return HTMLResponse(content=html)
