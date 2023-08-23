""" FastAPI로 ASGI app 객체 생성 """
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend import api

app = FastAPI(title="ECONOX API")

# ================= backend =================
app.include_router(api.router)

# ================= frontend =================
app.mount("/static", StaticFiles(directory="frontend/static"))


@app.get("/{all:path}", tags=["Frontend Hosting"])  # SPA Svelte APP hosting
def svelte_application() -> HTMLResponse:
    html = Path("frontend/static/index.html").read_text()
    return HTMLResponse(content=html)
