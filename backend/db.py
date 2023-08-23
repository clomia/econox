import json

import boto3
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
    except psycopg.OperationalError as e:  # password authentication failed
        # Secrets Manager에서 암호 교체가 이루어졌다고 간주하고 암호 업데이트 후 재시도
        latest_password = json.loads(
            boto3.client("secretsmanager").get_secret_value(
                SecretId=SECRETS["RDS_SECRET_MANAGER_ARN"]
            )["SecretString"]
        )["password"]
        SECRETS["DB_PASSWORD"] = latest_password
        log.warning(f"[{e}] DB 연결 오류가 발생하였습니다. Secrets Manager로부터 암호를 업데이트하여 재시도합니다.")
        return execute_query(query)
    except Exception as e:
        conn.rollback()
        log.critical(f"[{e}] DB 쿼리 실행 오류가 발생하여 롤백하였습니다.\nQuery: {query}")
        raise e
    finally:
        cur.close()
        conn.close()
