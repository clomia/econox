""" 
- sql 파일을 실행합니다. 
- [DB이름].sql 형식으로 파일을 관리하세요
"""
from pathlib import Path
from datetime import datetime

import psycopg

host = input("host: ")
password = input("password: ")
sql_path = Path(input("SQL path: "))
_dbname = sql_path.stem
dbname = input(f"db name [Default: {_dbname}]: ") or _dbname

sql = sql_path.read_text()
print(f"\n(SQL 코드 검토)\n\n{sql}\n\n")
input(f"실행 하시겠습니까? db name: {dbname}  ( Enter / Ctrl+C )\n")
conn = psycopg.connect(
    host=host,
    dbname=dbname,
    user="postgres",
    password=password,
)

try:
    cursor = conn.execute(sql)
except Exception as e:
    conn.rollback()
    print("에러가 발생하여 모든 요청을 안전하게 취소하였습니다.")
    raise e
else:
    conn.commit()
    print("SQL 실행 완료!")
finally:
    conn.close()

# ========== SQL 코드에 커밋 일시 기록 ==========ㄴ
timestring = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
record_line = f"--- Last commit: {timestring} ---"
sql_lines = sql.split("\n")
if "--- Last commit" not in sql_lines[0]:
    sql_path.write_text(f"{record_line}\n{sql}")
else:  # -> 과거에 기록된 일시 지우고 다시쓰기
    sql_lines[0] = record_line
    sql_path.write_text("\n".join(sql_lines))
