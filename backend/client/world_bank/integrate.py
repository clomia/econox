""" 모든 data_class를 Country 객체로 통합 """
import json
from typing import List
from functools import partial, lru_cache

import wbdata

from backend.compute import parallel
from backend.system import INFO_PATH
from backend.client.translate import Multilingual, translator
from backend.client.world_bank.data_class import *


def wbdata_safe_caller(wb_func):
    """
    - wbdata 함수가 안전하게 작동하도록 감쌉니다.
    - wbdata 라이브러리의 캐싱 알고리즘은 thread-safe하지 않으므로
    항상 cache=False 해줘야 하며, 결과가 없을 때 RuntimeError를 발생시키는데
    에러를 발생시키는 대신에 빈 리스트를 반환하도록 변경합니다.
    """

    def wrapper(*args, **kwargs):
        try:
            return wb_func(*args, **kwargs, cache=False)
        except RuntimeError:
            return []

    return wrapper


search_countries = wbdata_safe_caller(wbdata.search_countries)
get_country = wbdata_safe_caller(wbdata.get_country)


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
        if info := get_country(self.code):
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
    def longitude(self) -> float | None:
        return self.info["longitude"]

    @property
    def latitude(self) -> float | None:
        return self.info["latitude"]


@lru_cache(maxsize=1024)
def search(text: str) -> List[Country]:
    """is_valid가 False인 Country는 리스트에서 제외됩니다."""
    en_text = translator(text, to_lang="en")
    res = parallel.executor(  # 번역 한거, 안한거 전부 사용해서 검색
        partial(search_countries, text),
        partial(get_country, text),
        partial(search_countries, en_text),
        partial(get_country, en_text),
    )  # 여러 방법으로 검색하므로 합치면 중복 있음, set comprehension을 통해 중복 제거
    iso_codes = {country["id"] for countries in res.values() for country in countries}
    country_generators = [partial(Country, code) for code in iso_codes]
    countires = parallel.executor(*country_generators).values()
    return [country for country in countires if country.is_valid]
