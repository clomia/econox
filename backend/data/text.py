""" 텍스트 데이터 처리 모듈: Google Translate API 를 사용하는 다국어 객체 구현"""
from functools import partial

import deepl

from backend.http import deepl_translate
from backend.system import SECRETS


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
        return await deepl_translate(self.text, from_lang="en", to_lang=to)
