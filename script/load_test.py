"""
- 서버 부하 테스트 클라이언트
"""
import asyncio
import time
from datetime import datetime

import httpx

default_host = "https://www.econox.io"
host = input(f"HOST URL [Default: {default_host}]: ")
host = default_host if not host else host

email = input("Login Email: ")
password = input("Login password: ")

api_count = {"sucess": 0, "failure": 0}


def log(s: str):
    time_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"[{time_str}] {s}")


with httpx.Client(base_url=host) as client:
    try:
        resp = client.post(
            "/api/auth/user",
            json={"email": email, "password": password},
        )
        resp.raise_for_status()
        cognito_token = resp.json()["cognito_token"]
    except Exception as e:
        api_count["failure"] += 1
        log("[인증 토큰 발급 실패] 이메일과 비밀번호가 잘못되었습니다!")
        raise e
    else:
        api_count["sucess"] += 1
        log("인증 토큰 발급 성공\n")
token = f"Bearer {cognito_token}"


async def get(path, params: dict = {}) -> dict | list:
    async with httpx.AsyncClient(
        base_url=host, headers={"Authorization": token}
    ) as client:
        try:
            resp = await client.get(path, params=params)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            api_count["failure"] += 1
            log(f"[실패 응답 수신][GET {path}] -> [상태코드: {resp.status_code}] {resp.content}")
            raise e
        else:
            api_count["sucess"] += 1
            return resp.json()


async def post(path, payload: dict, params: dict = {}) -> dict | list:
    async with httpx.AsyncClient(
        base_url=host, headers={"Authorization": token}
    ) as client:
        try:
            resp = await client.post(path, json=payload, params=params)
            resp.raise_for_status()
        except httpx.HTTPStatusError as e:
            api_count["failure"] += 1
            log(f"[실패 응답 수신][POST {path}] -> [상태코드: {resp.status_code}] {resp.content}")
            raise e
        else:
            api_count["sucess"] += 1
            return resp.json()


async def get_factors(element_code, element_section, lang: str) -> list:
    page = 0
    factors = []
    while True:
        page += 1
        resp = await get(
            "/api/feature/factors",
            params={
                "element_code": element_code,
                "element_section": element_section,
                "lang": lang,
                "page": page,
            },
        )
        factors.extend(resp["factors"])
        if page == (total_page := resp["pages"]):
            log(f"[Factor 수집 완료] ({element_code})")
            break
        else:
            log(f"[Factor 수집중...] ({element_code}) -> ({page}/{total_page})")
    return factors


# ==================== Test functions ====================


async def test_search_tool(query: str, lang: str):
    """Element 검색 & 검색된 모든 Symbol에 대한 뉴스 가져오기"""
    resp = await get("/api/data/elements", params={"query": query, "lang": lang})
    get_news_tasks = []
    for symbol in resp["symbols"]:
        get_news_tasks.append(
            get("/api/data/news", params={"symbol": symbol["code"], "lang": lang})
        )
    start = time.time()
    await asyncio.gather(*get_news_tasks)
    spend = time.time() - start
    log(
        f"[FMP 뉴스 검색 완료] [쿼리:{query}, 언어: {lang}] [{spend:.3f}초] "
        f"[대상 Symbol 갯수: {len(get_news_tasks)}개]"
    )


async def test_univariate_tool(lang: str):
    """유저에 저장된 Element가져와서 모든 Element에 대한 모든 Factor 정의 가져오기"""
    element_list = await get("/api/feature/user/elements", params={"lang": lang})
    get_factor_tasks = []
    for ele in element_list:
        get_factor_tasks.append(get_factors(ele["code"], ele["section"], lang))
    start = time.time()
    all_factors = []
    for factors in await asyncio.gather(*get_factor_tasks):
        all_factors.extend(factors)
    spend = time.time() - start
    log(
        f"[유저에 저장된 모든 Element에 대한 모든 Factor 정의 수집 완료] [언어: {lang}] [{spend:.3f}초] "
        f"[수집된 Factor 갯수: {len(all_factors)}개]"
    )


async def tesk_all(lang: str, search_queries: list, univariate_tool_count: int = 1):
    """
    - lang: 언어
    - search_queries: 검색창에 쓸 검색어들
    - univariate_tool_count: 단변량 툴을 로딩하는 텝 갯수
        - 브라우저 텝 여러개가 동시에 요청하는 시나이로 시뮬레이션
    """
    log("부하 테스트 시작")
    start = time.time()
    await asyncio.gather(
        asyncio.gather(*[test_search_tool(query, lang) for query in search_queries]),
        *[test_univariate_tool(lang) for _ in range(univariate_tool_count)],
    )
    spend = time.time() - start
    log(
        "부하테스트 종료 "
        f"[{spend:.3f}초] [{api_count['sucess']}개 API 처리 성공] [{api_count['failure']}개 API 처리 실패]"
    )


# ==================== execute ====================
default_lang = "ko"
lang = input(f"언어 지정 (iso alpha-2 code) [Default: {default_lang}]: ")
lang = default_lang if not lang else lang
if len(lang) != 2:
    raise Exception("잘못된 언어 코드입니다!")
search_queries = []
while query := input(
    f"[검색 기능 테스트][누적된 검색어 {len(search_queries)}개] 검색어 입력 (공백 입력 시 종료): "
):
    search_queries.append(query)

try:
    _input = int(input("단변량 툴 탭 갯수[Default: 1]: "))
    univariate_tool_count = int(_input) if _input else 1
except ValueError as e:
    log(f"{_input}은 숫자가 아닙니다. 숫자를 입력하세요!")
    raise e

asyncio.run(tesk_all(lang, search_queries, univariate_tool_count))
