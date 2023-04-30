import os
import threading
import queue
from typing import List, Callable

from .space import HuggingfaceSpace


class SpacePool:

    def __init__(self, size: int = 0):
        self._threads: List[threading.Thread] = []
        self._do_stop = None
        self._queue = queue.Queue()
        self._size = size or os.cpu_count()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    @property
    def size(self) -> int:
        return self._size

    def running(self) -> bool:
        return bool(self._threads)

    def start(self):
        if self.running():
            return

        self._do_stop = False
        self._start()

    def stop(self, join_queue: bool = True):
        if not self.running() or self._do_stop:
            return

        self._queue.put({"stop": True})

        if join_queue:
            self._queue.join()

        self._do_stop = True
        self._stop()

    def run(self, space: HuggingfaceSpace):
        self._queue.put_nowait({"space": space})

    def _start(self):
        self._threads = [
            threading.Thread(name=f"{self.__class__.__name__}-{i+1}/{self.size}", target=self._mainloop)
            for i in range(self._size)
        ]
        for t in self._threads:
            t.start()

    def _stop(self):
        for t in self._threads:
            t.join()

    def _mainloop(self):
        while not self._do_stop:
            try:
                action = self._queue.get(timeout=.5)

                if action.get("space"):
                    action["space"].run()

                if action.get("stop"):
                    self._do_stop = True

                self._queue.task_done()
            except queue.Empty:
                pass
