import asyncio
from backend.data.text import Multilingual


async def func():
    hello = Multilingual("hello")
    k = await hello.ko()
    print(k)


asyncio.run(func())
