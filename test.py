import asyncio
from backend import db


async def func():
    sql1 = db.SQL(
        "INSERT INTO elements (section, code) VALUES ({symbol}, {code})",
        params={"symbol": "country", "code": "AAPL"},
        fetch=False,
    )
    sql2 = db.SQL("SELECT * FROM elements")
    r = await db.exec(sql1, sql2)
    print(r)


asyncio.run(func())
