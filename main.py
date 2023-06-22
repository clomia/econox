import os
import subprocess
from datetime import datetime

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

print("업데이트 버전 서버 작동!")

templates = Jinja2Templates(directory="templates")


def list_files_html(startpath):
    html_string = "<html>\n<body>\n"

    df_str = subprocess.run(
        ["df", "-h"], stdout=subprocess.PIPE, check=True
    ).stdout.decode()
    lst = df_str.split("\n")
    df_html = "".join([f"<div>{o}</div>" for o in lst])

    ls_str = subprocess.run(["ls"], stdout=subprocess.PIPE, check=True).stdout.decode()
    ls_html = f"<div>{ls_str}</div>"

    html_string += df_html
    html_string += ls_html

    for root, dirs, files in os.walk(startpath):
        level = root.replace(startpath, "").count(os.sep)
        indent = " " * 4 * (level)
        html_string += "{}<b>{}/</b><br>\n".format(indent, os.path.basename(root))
        subindent = " " * 4 * (level + 1)
        for f in files:
            html_string += "{}{}<br>\n".format(subindent, f)

    html_string += "</body>\n</html>"

    # HTML 문자열 반환
    return html_string


@app.get("/", response_class=HTMLResponse)
async def hello_world():
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] /에 요청 들어옴")
    html_result = list_files_html(".")
    return html_result


@app.get("/items/{id}", response_class=HTMLResponse)
async def read_item(request: Request, id: str):
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{now}] {request}, {id} 요청 들어옴!")
    return templates.TemplateResponse("item.html", {"request": request, "id": id})
