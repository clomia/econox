import asyncio
from backend.data.text import Multilingual


async def func():
    hello = Multilingual("hello")
    k = await hello.ko()
    new = Multilingual("new")

    print(k)
    print(await new.ko())


asyncio.run(func())
