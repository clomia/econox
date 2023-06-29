""" FastAPI로 ASGI app 객체 생성 """
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

import routers

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"))
routers.regist(app)
