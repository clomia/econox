""" 모든 data_class를 Country 객체로 통합 """
import json
from typing import Tuple, List
from functools import partial, lru_cache

import wbdata

from config import LRU_CACHE_SIZE, INFO_PATH
from compute.parallel import ParallelManager
from client.translate import Multilingual, translator
from client.world_bank.data_class import Trade, Natural, Population, Industry, Economy


class Country:
    def __init__(self, code: str):
        """code: ISO 3166-1 alpha-3 국가코드"""
        self.code = code
        self.info_path = INFO_PATH / f"country/{code}.json"
        self.info = self.get_info()
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
        try:
            info = wbdata.get_country(self.code, cache=False)
        except RuntimeError:
            name = region = capital = income = longitude = latitude = None
        else:
            name = info[0].get("name")
            region = info[0]["region"].get("value")
            capital = info[0].get("capitalCity")
            income = info[0]["incomeLevel"].get("value")
            longitude = info[0].get("longitude")
            latitude = info[0].get("latitude")

        # ======= 수집된 데이터 정제 =======
        if name and region and capital and income:  # 이 4가지 정보는 필수
            note = f"{name} is located in {region} and its capital is {capital} The income level is {income}"
            info = {"name": name, "note": note}
        elif name:
            info = {"name": name, "note": f"{name}({self.code}): No information"}
        else:
            no_info_expr = f"{self.code}: No information"
            info = {"name": no_info_expr, "note": no_info_expr}
        info |= {  # 경위도 정보 추가
            "longitude": float(longitude) if longitude else None,
            "latitude": float(latitude) if latitude else None,
        }
        self.info_path.parent.mkdir(parents=True, exist_ok=True)
        json.dump(info, self.info_path.open("w"))  # EFS volume에 저장
        return info

    @property
    def name(self):
        return Multilingual(self.info["name"])

    @property
    def note(self):
        return Multilingual(self.info["note"])

    @property
    def longitude(self) -> Tuple[float]:
        return self.info["longitude"]

    @property
    def latitude(self):
        return Multilingual(self.info["latitude"])


@lru_cache(maxsize=LRU_CACHE_SIZE)
def search(text: str) -> List[Country]:
    en_text = translator(text, to_lang="en")
    manager = ParallelManager()
    manager.regist(  # 번역 한거, 안한거 전부 사용해서 검색
        partial(wbdata.search_countries, text, cache=False),
        partial(wbdata.get_country, text, cache=False),
        partial(wbdata.search_countries, en_text, cache=False),
        partial(wbdata.get_country, en_text, cache=False),
    )
    results = manager.execute()
    countries = []
    for result in results.values():
        if result:
            countries += result
    return [Country(code=country["id"]) for country in countries]
