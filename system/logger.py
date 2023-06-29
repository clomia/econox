import logging
import logging.config
from datetime import datetime


class LogHandler(logging.NullHandler):
    def __init__(self):
        super().__init__()

    def handle(self, record):
        now = datetime.now()
        time = f"{now.month}/{now.day} {now.hour}시 {now.minute}분 {now.second}초"
        content = f"[{record.levelname}][{time}] {self.format(record)}"
        print(content)


log = logging.getLogger("app")
log.propagate = False  # FastAPI나 Uvicorn 등 다른 로깅 출력에 전파되지 않도록
log.setLevel(logging.DEBUG)
formatter = logging.Formatter("%(message)s")
log_handler = LogHandler()
log_handler.setFormatter(formatter)
log_handler.setLevel(logging.DEBUG)
log.addHandler(log_handler)
