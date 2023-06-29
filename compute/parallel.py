import asyncio
from typing import Callable, Any, Dict
from concurrent.futures import ThreadPoolExecutor


async def async_executor(*functions) -> Dict[Callable[[], Any], Any]:
    """쓰레드 풀을 통해 함수들을 병렬로 처리하는 await 가능한 비동기 함수입니다."""
    with ThreadPoolExecutor() as executor:
        loop = asyncio.get_running_loop()
        futures = [loop.run_in_executor(executor, func) for func in functions]
        results = await asyncio.gather(*futures)
    return dict(zip(functions, results))


def executor(*functions):
    """쓰레드 풀을 통해 함수들을 병렬로 처리합니다."""
    pool = ThreadPoolExecutor()
    results = list(pool.map(lambda func: func(), functions))
    return dict(zip(functions, results))
