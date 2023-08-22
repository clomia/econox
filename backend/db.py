import psycopg

from backend.system import SECRETS, log


def execute_query(query: str) -> list:
    try:
        conn = psycopg.connect(
            host=SECRETS["DB_HOST"],
            dbname=SECRETS["DB_NAME"],
            user=SECRETS["DB_USERNAME"],
            password=SECRETS["DB_PASSWORD"],
        )
        cur = conn.cursor()
        cur.execute(query)
        conn.commit()
        return cur.fetchall()  # case: read success
    except psycopg.ProgrammingError as e:
        return []  # case: write success
    except Exception as e:
        conn.rollback()
        log.critical(f"DB 쿼리 실행 오류가 발생하여 롤백하였습니다. {e}\n{query}")
        raise e
    finally:
        cur.close()
        conn.close()
