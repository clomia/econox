""" FastAPI로 ASGI app 객체 생성 """

from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from backend import api, system
from backend.integrate import lang_exception_handler


app = FastAPI(
    title="Econox API",
    description="Econox Application server",
    docs_url="/api" if system.is_local else None,
    redoc_url="/document" if system.is_local else None,
)

# ================= backend =================
set_middleware = app.middleware("http")
set_middleware(lang_exception_handler)

for router in api.routers:
    app.include_router(router)

# ================= frontend =================
app.mount("/static", StaticFiles(directory="frontend/static"))


@app.get("/{all:path}", tags=["Frontend Hosting"], description="SPA Svelte app hosting")
def svelte_application() -> HTMLResponse:
    html = Path("frontend/static/index.html").read_text()
    return HTMLResponse(content=html)
