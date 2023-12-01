import asyncio

from backend import db


async def func():
    sql = db.InsertSQL("factors", section="hello", code="he", name="안녕", note="노트")
    r = sql.encode()
    # r = await sql.exec()
    print(r)


asyncio.run(func())
