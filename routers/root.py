import os
import subprocess

from fastapi import APIRouter
from fastapi.responses import HTMLResponse


router = APIRouter()


@router.get("/", response_class=HTMLResponse)
def hello_world():
    startpath = "."
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
    return html_string
