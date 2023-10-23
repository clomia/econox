"""
- 번역 용어집
- backend.http 모듈의 번역 API 함수에서 인공지능 번역의 불완전한 부분을 보완하는데 사용됩니다.
- 이 디렉토리에 {출발어}-{목적어}.json 파일을 생성하여 용어집을 생성하세요 (언어는 ISO 639-1 표기를 따라야 함)
"""
import json
from pathlib import Path
from collections import defaultdict

glossaries = {}
for path in Path(__file__).parent.glob("*.json"):
    with path.absolute().open() as file:
        data = json.load(file)
    glossaries[path.stem] = data


# to_lang을 키로 하는 딕셔너리를 생성합니다. 언어 감지를 사용하기 때문에 from_lang-to_lang을 키로 사용할 수 없습니다.
dictionaries = defaultdict(dict)
for name, glossary in glossaries.items():
    key = name.split("-")[-1]
    for _from, _to in glossary.items():
        dictionaries[key][_from] = _to
