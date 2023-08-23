import json

import boto3
import requests
import psycopg

from backend.system import SECRETS, log


jwks_url = f"https://cognito-idp.us-east-1.amazonaws.com/{SECRETS['COGNITO_USER_POOL_ID']}/.well-known/jwks.json"
jwks = requests.get(jwks_url).json()
# 로그인된 유저가 요청 헤더에 담는 토큰을 보고 검사 & 누구인지 확인하는 라우터 전처리 함수(인터셉터) 만들어야 함


def db_exec_query(query: str) -> list:
    """RDS Database에 SQL 쿼리를 실행하고 결과를 반환합니다."""
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
        return db_exec_query(query)
    except Exception as e:
        conn.rollback()
        log.critical(f"[{e}] DB 쿼리 실행 오류가 발생하여 롤백하였습니다.\nQuery: {query}")
        raise e
    finally:
        cur.close()
        conn.close()
