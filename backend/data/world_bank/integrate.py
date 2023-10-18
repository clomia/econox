""" 모든 data_class를 Country 객체로 통합 """
import json
import asyncio
from typing import List

from backend.http import WorldBankAPI
from backend.system import EFS_VOLUME_PATH
from backend.data.text import Multilingual, translator
from backend.data.world_bank.data_class import *

INFO_PATH = EFS_VOLUME_PATH / "info"


class Country:
    def __init__(self, code: str):
        """
        - code: ISO 3166-1 alpha-3 국가코드
        - 인스턴스 생성 방법
            - `usa = await Country("USA").load()`
        - 경고! load 안하면 데이터 조회 못함
        """
        self.api = WorldBankAPI()
        self.code = code
        self.info_path = INFO_PATH / f"country/{code}.json"
        self.info = {"name": None, "note": None}
        self.is_valid = False

        self.trade = Trade(code)
        self.natural = Natural(code)
        self.population = Population(code)
        self.industry = Industry(code)
        self.economy = Economy(code)

    def __repr__(self) -> str:
        return f"<Country: {self.code}>"

    async def load(self):
        info, *_ = await asyncio.gather(
            self.get_info(),
            self.trade.load_factor(),
            self.natural.load_factor(),
            self.population.load_factor(),
            self.industry.load_factor(),
            self.economy.load_factor(),
        )
        self.info = info
        self.is_valid = self.info["name"] and self.info["note"]
        return self

    async def get_info(self):
        # ======= EFS volume 에서 가져오기 =======
        if self.info_path.exists():  # 볼륨에서 가져오기
            return json.load(self.info_path.open("r"))

        # ======= API 사용해서 데이터 수집 =======
        if info := (await self.api.get_country(self.code)):
            name = info.get("name")
            region = info["region"].get("value")
            capital = info.get("capitalCity")
            income = info["incomeLevel"].get("value")
            longitude = info.get("longitude")
            latitude = info.get("latitude")
        else:
            name = region = capital = income = longitude = latitude = None
        # ======= 수집된 데이터 정제 =======
        note = None
        if name and region and capital and income:  # 이 4가지 정보는 필수
            note = f"{name}({self.code}) is located in {region} and its capital is {capital} The income level is {income}."
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


async def search(text: str) -> List[Country]:
    """is_valid가 False인 Country는 리스트에서 제외됩니다."""
    api = WorldBankAPI()

    en_text = await translator(text, to_lang="en")
    *l1, l2, l3 = await asyncio.gather(  # 번역 한거, 안한거 전부 사용해서 검색
        api.get_country(text),  # -> dict - in l1
        api.get_country(en_text),  # -> dict - in l1
        api.search_countries(text),  # -> List[dict] - to l2
        api.search_countries(en_text),  # -> List[dict] - to l3
    )  # 여러 방법으로 검색하므로 합치면 중복 있음, set을 통해 중복 제거
    iso_codes = {country["id"] for country in list(l1) + l2 + l3 if country}
    countires = await asyncio.gather(*(Country(code).load() for code in iso_codes))
    return sorted(
        [country for country in countires if country.is_valid],
        key=lambda country: len(country.name.text),  # 국가명이 짧은게 위로 오도록
    )
