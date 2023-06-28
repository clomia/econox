import queue
import threading
from typing import Callable, Any


class AsyncExecutor:
    def __init__(self, *functions: Callable[[], Any]):
        """
        - 비동기 실행 대상 함수를 등록합니다.
        - 함수는 아무런 인자도 받지 않아야 합니다. functools.partial 모듈을 활용하세요
        """
        self.workers = []
        self.queue = queue.Queue()

        for func in functions:
            worker = threading.Thread(target=self._wrapper, args=[func])
            self.workers.append(worker)

    def _wrapper(self, func):
        result = func()
        self.queue.put((func, result))

    def execute(self):
        """
        - 등록된 함수들을 비동기적으로 실행합니다. (단일 CPU가 놀지 않도록)
        - return: 함수의 반환값을 담은 딕셔너리가 { 함수객체:결과 } 형태로 반환됩니다."""
        for worker in self.workers:
            worker.start()
        results = {}
        for _ in self.workers:
            key, value = self.queue.get()
            results[key] = value
        return results
