""" 모든 data_class를 Country 객체로 통합 """
import asyncio
from typing import List

from aiocache import cached

from backend.http import WorldBankAPI
from backend.system import ElasticRedisCache, CacheTTL
from backend.data.text import Multilingual, translate
from backend.data.world_bank.data_class import *


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
        self.info = {"name": None, "note": None}
        self.is_valid = False
        (
            self.trade,
            self.natural,
            self.population,
            self.industry,
            self.economy,
        ) = self.sections = [
            Trade(code),
            Natural(code),
            Population(code),
            Industry(code),
            Economy(code),
        ]

    def __repr__(self) -> str:
        return f"<Country: {self.code}>"

    def factors(self) -> List[dict]:
        """
        - Country에 대한 모든 펙터를 반환
        - return: [ { code, name, note, section: {code, name, note} }, ... ]
        """
        factors = []
        for section in self.sections:
            for factor_code in section.indicator_codes.values():
                factor = getattr(section, factor_code)
                factors.append(
                    {
                        "code": factor_code,
                        "name": factor.name,
                        "note": factor.note,
                        "section": {
                            "code": section.__class__.__name__,
                            "name": section.name,
                            "note": section.note,
                        },
                    }
                )
        return factors

    async def load(self):
        info, *_ = await asyncio.gather(
            self.get_info(), *[section.load_factor() for section in self.sections]
        )
        self.info = info
        self.is_valid = self.info["name"] and self.info["note"]
        return self

    @cached(cache=ElasticRedisCache, ttl=CacheTTL.MAX)
    async def get_info(self):
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


async def search(text: str, limit: int = 3) -> List[Country]:
    """
    - is_valid가 False인 Country는 리스트에서 제외됩니다.
    - limit: 검색 갯수 제한 (World bank 약해서 한번에 너무 많이 하면 안돼)
    """
    api = WorldBankAPI()

    en_text = await translate(text, to_lang="en")
    *l1, l2, l3 = await asyncio.gather(  # 번역 한거, 안한거 전부 사용해서 검색
        api.get_country(text),  # -> dict - in l1
        api.get_country(en_text),  # -> dict - in l1
        api.search_countries(text),  # -> List[dict] - to l2
        api.search_countries(en_text),  # -> List[dict] - to l3
    )  # 여러 방법으로 검색하므로 합치면 중복 있음, set을 통해 중복 제거
    # text가 국가 코드인 경우 l1에 들어가므로 슬라이싱해도 유지됨 그니까 재정렬 안해도 됌
    iso_code_set = {country["id"] for country in list(l1) + l2 + l3 if country}
    target_list = list(iso_code_set)[:limit]
    countires = await asyncio.gather(*(Country(code).load() for code in target_list))
    return sorted(
        [country for country in countires if country.is_valid],
        key=lambda country: len(country.name.text),  # 국가명이 짧은게 위로 오도록
    )
