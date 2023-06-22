""" 모든 data_class를 Country 객체로 통합 """
from typing import Tuple, List

import wbdata

from client.translate import Multilingual, translator
from client.world_bank.data_class import Trade, Natural, Population, Industry, Economy


class Country:
    def __init__(self, code: str):
        """code: ISO 3166-1 alpha-3 국가코드"""
        self.code = code
        self.trade = Trade(code)
        self.natural = Natural(code)
        self.population = Population(code)
        self.industry = Industry(code)
        self.economy = Economy(code)

    def __repr__(self) -> str:
        return f"<Country: {self.code}>"

    @property
    def info(self):
        name = note = income_level = "No information"
        lnglat = (0, 0)
        try:
            info = wbdata.get_country(self.code, cache=True)
        except RuntimeError:
            pass
        else:
            name = info[0]["name"]
            if (lng := info[0]["longitude"]) and (lat := info[0]["latitude"]):
                lnglat = (float(lng), float(lat))
                region = info[0]["region"]["value"]
                capital = info[0]["capitalCity"]
                note = f"The {name} is in {region} and the capital is {capital}"
                income_level = info[0]["incomeLevel"]["value"]
        return {
            "name": name,
            "note": note,
            "lnglat": lnglat,
            "income_level": income_level,
        }

    @property
    def name(self):
        """Country에 대한 이름"""
        return Multilingual(self.info["name"])

    @property
    def note(self):
        """Country에 대한 설명"""
        return Multilingual(self.info["note"])

    @property
    def lnglat(self) -> Tuple[float]:
        """Country에 대한 위치(경위도)"""
        return self.info["lnglat"]

    @property
    def income_level(self):
        """Country에 대한 소득 수준"""
        return Multilingual(self.info["income_level"])


def search(text: str, limit: int = 10) -> List[Country]:
    en_text = translator(text, to_lang="en")
    countries = wbdata.search_countries(en_text, cache=True)
    return [Country(code=country["id"]) for country in countries][:limit]
