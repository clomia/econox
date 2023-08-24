""" Google Translate API 를 사용하는 다국어 객체 구현"""
import os
import html
import logging
from functools import partial

from aiocache import cached
from google.cloud import translate_v2

from backend.system import Parallel, EFS_VOLUME_PATH, SECRETS

# 빠른 병렬 처리로 인해 아래와 같은 경고가 뜨므로 해당 경고 로그가 뜨지 않도록 합니다.
# WARNING:urllib3.connectionpool:Connection pool is full, discarding connection: translation.googleapis.com. Connection pool size: 10
logging.getLogger("urllib3.connectionpool").setLevel(logging.ERROR)

# GCP Credential 등록
gcp_credential_path = EFS_VOLUME_PATH / "gcp_credential.json"
gcp_credential_path.write_text(SECRETS["GCP_CREDENTIAL_JSON"])
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(gcp_credential_path)

google_translator = translate_v2.Client()


@cached(ttl=12 * 360)
async def translator(text: str, to_lang: str, *, from_lang: str = None) -> str:
    """
    - 자연어를 번역합니다.
    - text: 자연어 문자열
    - to_lang: 목적 언어의 ISO 639-1 코드
    - from_lang[optional]: text의 언어 ISO 639-1 코드
        - 기본: None -> 언어감지
    """
    resp = await Parallel(Async=True).execute(
        partial(
            google_translator.translate,
            text,
            source_language=from_lang,
            target_language=to_lang,
        )
    )
    # 응답 데이터가 S&P500에서 &을 &amp; 라고 표현하는 등 HTML 이스케이프 표현을 쓰기 때문에 unescape 해야 함
    return html.unescape(resp["translatedText"])


class Multilingual:
    """
    - 문자열에 대한 다국어 객체
    - `hello = Multilingual("hello")`
    - `안녕 = await hello.ko()`
    """

    supported_langs = google_translator.get_languages()

    def __init__(self, text: str):
        """
        - text: 영어 문자열
            - 영어 -> 다국어가 표현력이 가장 좋기 때문에 base는 무조건 영어로 합니다.
        """
        self.text = text

    def __repr__(self) -> str:
        text_repr = self.text if len(self.text) <= 30 else self.text[:30] + "..."
        return repr(f"<Multilingual: {text_repr}>")

    async def trans(self, to: str):
        if to == "en":
            return self.text
        return await translator(self.text, from_lang="en", to_lang=to)


# Multilingual 클래스에 번역 가능한 모든 iso 코드로 property를 생성합니다
for lang in Multilingual.supported_langs:
    iso_code = lang["language"]
    obj = partial(Multilingual.trans, to=iso_code)
    setattr(Multilingual, iso_code, obj)
