""" 모든 data_class를 Country 객체로 통합 """
import json
from typing import List
from functools import partial, lru_cache

import wbdata  #! wbdata 라이브러리의 캐싱 알고리즘은 thread-safe하지 않으므로 항상 cache=False 해줘야 한다!

from backend.system import LRU_CACHE_SIZE, INFO_PATH
from backend.compute import parallel
from backend.client.translate import Multilingual, translator
from backend.client.world_bank.data_class import (
    Trade,
    Natural,
    Population,
    Industry,
    Economy,
)


def runtime_error_handler(func):
    """
    wbdata 모듈을 검색 결과가 없을 때 RuntimeError를 반환합니다.
    따라서 RuntimeError가 발생하면 빈 리스트를 반환하도록 함수를 감쌉니다.
    """

    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
        except RuntimeError:
            result = []
        return result

    return wrapper


search_countries = runtime_error_handler(wbdata.search_countries)
get_country = runtime_error_handler(wbdata.get_country)


class Country:
    def __init__(self, code: str):
        """code: ISO 3166-1 alpha-3 국가코드"""
        self.code = code
        self.info_path = INFO_PATH / f"country/{code}.json"
        self.info = self.get_info()
        self.is_valid = self.info["name"] and self.info["note"]

        self.trade = Trade(code)
        self.natural = Natural(code)
        self.population = Population(code)
        self.industry = Industry(code)
        self.economy = Economy(code)

    def __repr__(self) -> str:
        return f"<Country: {self.code}>"

    def get_info(self):
        # ======= EFS volume 에서 가져오기 =======
        if self.info_path.exists():  # 볼륨에서 가져오기
            return json.load(self.info_path.open("r"))

        # ======= API 사용해서 데이터 수집 =======
        if info := get_country(self.code, cache=False):
            name = info[0].get("name")
            region = info[0]["region"].get("value")
            capital = info[0].get("capitalCity")
            income = info[0]["incomeLevel"].get("value")
            longitude = info[0].get("longitude")
            latitude = info[0].get("latitude")
        else:
            name = region = capital = income = longitude = latitude = None
        # ======= 수집된 데이터 정제 =======
        note = None
        if name and region and capital and income:  # 이 4가지 정보는 필수
            note = f"{name}({self.code}) is located in {region} and its capital is {capital} The income level is {income}"
        info = {"name": name, "note": note}
        info |= {  # 경위도 정보 추가
            "longitude": float(longitude) if longitude else None,
            "latitude": float(latitude) if latitude else None,
        }
        self.info_path.parent.mkdir(parents=True, exist_ok=True)
        json.dump(info, self.info_path.open("w"))  # EFS volume에 저장
        return info

    @property
    def name(self):
        _name = self.info["name"]
        return Multilingual(_name if _name else f"{self.code}: No information")

    @property
    def note(self):
        _note, _name = self.info["note"], self.info["name"]
        if _note:
            return Multilingual(_note)
        elif _name:
            return Multilingual(f"{_name}({self.code}): No information")
        else:
            return Multilingual(f"{self.code}: No information")

    @property
    def longitude(self) -> float:
        return self.info["longitude"]

    @property
    def latitude(self) -> float:
        return self.info["latitude"]


@lru_cache(maxsize=LRU_CACHE_SIZE)
def search(text: str) -> List[Country]:
    """is_valid가 False인 Country는 리스트에서 제외됩니다."""
    en_text = translator(text, to_lang="en")
    results = parallel.executor(  # 번역 한거, 안한거 전부 사용해서 검색
        partial(search_countries, text, cache=False),
        partial(get_country, text, cache=False),
        partial(search_countries, en_text, cache=False),
        partial(get_country, en_text, cache=False),
    )
    iso_code_set = {ele["id"] for result in results.values() for ele in result}
    countires = parallel.executor(
        *[partial(Country, code) for code in iso_code_set]
    ).values()
    return [country for country in countires if country.is_valid]
