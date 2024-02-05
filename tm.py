import os

os.environ["IS_LOCAL"] = "true"
# run.sh를 통해서 로컬에 Redis 서버도 켜줘야 함

import asyncio
from backend.integrate import Feature, FeatureGroup

table = FeatureGroup(
    "ko",
    Feature(
        element_section="symbol",
        element_code="META",
        factor_section="HistoricalPrice",
        factor_code="adj_close",
    ),
    Feature(
        element_section="symbol",
        element_code="GOOGL",
        factor_section="HistoricalPrice",
        factor_code="adj_close",
    ),
    Feature(
        element_section="symbol",
        element_code="NVDA",
        factor_section="HistoricalPrice",
        factor_code="adj_close",
    ),
)


async def func():
    return await table.to_dataframe()


data_arrays = asyncio.run(func())
print(data_arrays)
