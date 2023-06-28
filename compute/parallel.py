import queue
import threading
import multiprocessing
from typing import Callable, Any

multiprocessing.set_start_method("fork")


class ParallelManager:
    def __init__(self, GIL=True):
        """
        - 여러개의 함수를 병렬적으로 실행할 수 있도록 해줍니다.
        - GIL이 True인 경우 threading을 사용하고 False인 경우 multiprocessing를 사용합니다.
        """
        self.workers = []
        self.worker_obj = threading.Thread if GIL else multiprocessing.Process
        self.queue = queue.Queue() if GIL else multiprocessing.Queue()

    def regist(self, *functions: Callable[[], Any]):
        """
        - 병렬 실행 대상 함수를 등록합니다.
        - 함수는 아무런 인자도 받지 않아야 합니다. functools.partial 모듈을 활용하세요
        - 함수에서 예외가 발생한 경우 예외가 외부로 전파되지 않으며 결과로 None이 할당됩니다.
        """
        for func in functions:

            def _func(func):
                try:
                    result = func()
                except:
                    self.queue.put((func, None))
                else:
                    self.queue.put((func, result))

            worker = self.worker_obj(target=_func, args=[func])
            self.workers.append(worker)

    def execute(self):
        """
        - 등록된 함수들을 병렬적으로 실행합니다.
        - return: 함수의 반환값을 담은 딕셔너리가 { 함수객체:결과 } 형태로 반환됩니다."""
        for worker in self.workers:
            worker.start()
        results = {}
        for _ in self.workers:
            key, value = self.queue.get()
            results[key] = value
        return results
