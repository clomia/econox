import psycopg

from backend.system import SECRETS, log


def execute_query(query: str) -> list:
    conn = psycopg.connect(
        host=SECRETS["DB_HOST"],
        dbname=SECRETS["DB_NAME"],
        user=SECRETS["DB_USERNAME"],
        password=SECRETS["DB_PASSWORD"],
    )
    try:
        conn.execute(query)
    except Exception as e:
        conn.rollback()
        log.critical(f"DB 쿼리 실행 오류 발생 query: {query}")
        raise e
    else:
        conn.commit()
    finally:
        conn.close()
    cur = conn.cursor()
    try:
        return cur.fetchall()  # case: read success
    except psycopg.ProgrammingError:
        return []  # case: write success
