""" 텍스트 데이터 처리 모듈: DeepL Translate API 를 사용하는 다국어 객체 구현"""
import json
from pathlib import Path
from functools import partial
from collections import defaultdict

import deepl
import httpx
import redis.asyncio as redis

from backend.http import pooling
from backend.system import SECRETS, REDIS_CONFIG, CacheTTL

# - 번역 용어집: 인공지능 번역의 불완전한 부분을 보완하는데 사용됩니다.
# - 이 디렉토리에 {출발어}-{목적어}.json 파일로 용어집을 생성하세요 (언어 표기는 ISO 639-1 사용)
glossaries_json = {}
for path in Path(__file__).parent.glob("*.json"):
    with path.open() as file:
        glossaries_json[path.stem] = json.load(file)
# to_lang을 키로 하는 딕셔너리로 변환합니다. 언어 감지를 사용하기 때문에 from_lang을 키로 사용할 수 없습니다.
glossaries = defaultdict(dict)
for name, glossary in glossaries_json.items():
    to_lang = name.split("-")[-1]
    for from_txt, to_txt in glossary.items():
        glossaries[to_lang][from_txt] = to_txt


class DeeplCache:
    """
    - Redis를 백엔드로 사용합니다
    - 최대한 부하를 줄이기 위해 aiocache 안쓰고 커스텀해서 사용
    """

    expire = CacheTTL.MAX
    cache = redis.Redis(**REDIS_CONFIG)

    def __init__(self, to_lang: str, from_lang: str = None):
        self.key_prefix = f"{str(from_lang).lower()}-{to_lang.lower()}"

    def cache_key(self, s: str):
        return f"[{self.key_prefix}]{str(s)}"

    async def set(self, key: str, value: str):
        _key = self.cache_key(key)
        await self.cache.set(_key, str(value), ex=self.expire)

    async def get(self, key: str):
        value = await self.cache.get(self.cache_key(key))
        # Redis가 Bytes문자열을 줄때가 있음...
        return value.decode("utf-8") if isinstance(value, bytes) else value


async def translate(text: str, to_lang: str, *, from_lang: str = None) -> str:
    """deepl 공식 SDK쓰면 urllib 풀 사이즈 10개 제한 떠서 httpx 비동기 클라이언트로 별도의 함수 작성"""

    target = text.strip()

    if glossary := glossaries.get(to_lang):
        if result := glossary.get(target):
            return result  # 용어집에서 해당 도착어에 대해 일치하는 번역 정의를 찾으면 그것을 반환한다.

    cache = DeeplCache(to_lang, from_lang)
    if result := (await cache.get(target)):
        return result  # 캐싱된 결과가 있다면 그것을 반환한다.

    host = "https://api.deepl.com/v2/translate"
    variant_hendler = {
        "en": "EN-US",
        "pt": "PT-PT",
    }  # https://www.deepl.com/docs-api/translate-text/?utm_source=github&utm_medium=github-python-readme (Request Parameters부분의 source_lang, target_lang 섹션 참조)
    target_language = to_lang.upper()
    if to_lang in variant_hendler:
        target_language = variant_hendler[to_lang]
    source_language = from_lang.upper() if from_lang else None

    async def request():
        async with httpx.AsyncClient(timeout=15) as client:
            return await client.post(
                host,
                headers={
                    "Authorization": f"DeepL-Auth-Key {SECRETS['DEEPL_API_KEY']}",
                    "Content-Type": "application/json",
                },
                json={
                    "text": [target],
                    "target_lang": target_language,
                    "source_lang": source_language,
                },
            )

    try:
        resp = await pooling(
            request,  # https://www.deepl.com/ko/docs-api/api-access/error-handling
            inspecter=lambda resp: resp.status_code == 200,
            exceptions=Exception,
            timeout=20,
        )
    except (AssertionError, Exception) as e:
        raise httpx.HTTPError(f"DeepL 통신 오류 Error: {e} (사용량 한도에 도달했을 수 있습니다.)")
    else:
        result = resp.json()["translations"][0]["text"]
        await cache.set(key=target, value=result)
        return result


class Multilingual:
    """
    - 문자열에 대한 다국어 객체
    - `hello = Multilingual("hello")`
    - `안녕 = await hello.ko()`
    """

    supported_langs = deepl.Translator(
        auth_key=SECRETS["DEEPL_API_KEY"]
    ).get_source_languages()

    def __init__(self, text: str):
        """
        - text: 영어 문자열
            - 영어 -> 다국어가 표현력이 가장 좋기 때문에 base는 무조건 영어로 합니다.
        """
        self.text = text
        # Multilingual 클래스에 번역 가능한 모든 iso 코드로 property를 생성합니다
        for lang in self.supported_langs:
            iso_code = lang.code.lower()
            func = partial(self.trans, to=iso_code)
            setattr(self, iso_code, func)

    def __repr__(self) -> str:
        text_repr = self.text if len(self.text) <= 30 else self.text[:30] + "..."
        return repr(f"<Multilingual: {text_repr}>")

    async def trans(self, to: str):
        if to == "en":
            return self.text
        return await translate(self.text, from_lang="en", to_lang=to)
