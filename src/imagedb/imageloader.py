import os
import queue
from pathlib import Path
from threading import current_thread, Thread
from multiprocessing import Process, current_process, Manager
from functools import partial
from typing import List, Callable, Union, Iterable, Tuple, Optional, Dict

import PIL.Image

from src.image import resize_crop
from src import log


class ImageLoader:

    def __init__(
            self,
            size: int = 0,
            do_process: bool = False,
            verbose: bool = False,
    ):
        self._do_stop = None
        self._result_queue = queue.Queue()
        self._size = size or os.cpu_count()
        self._do_process = do_process
        self._verbose = verbose
        if self._do_process:
            self._manager = Manager()
            self._processes: List[Process] = []
            self._queue = self._manager.Queue()
        else:
            self._threads: Optional[List[Thread]] = None
            self._queue = queue.Queue()

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    @property
    def size(self) -> int:
        return self._size

    @property
    def do_process(self) -> bool:
        return self._do_process

    def load_images(
            self,
            filenames: Iterable[Union[str, Path]],
            resize: Optional[Tuple[int, int]] = None,
    ) -> Dict[str, dict]:
        result_mapping = {}
        for filename in filenames:
            filename = str(filename)
            result_mapping[filename] = None
            self._queue.put_nowait({"filename": filename, "resize": resize})

        while any(v is None for v in result_mapping.values()):
            try:
                result = self._result_queue.get(timeout=.01)
                filename = result.pop("filename")
                result_mapping[filename] = result
            except queue.Empty:
                pass

        return result_mapping

    def running(self) -> bool:
        return bool(self._processes) if self._do_process else bool(self._threads)

    def start(self):
        if self.running():
            return

        if self._verbose:
            self._log("starting workers")

        self._do_stop = False
        self._start()

    def stop(self):
        if not self.running() or self._do_stop:
            return

        if self._verbose:
            self._log("stopping workers")

        self._queue.put_nowait({"stop": True})
        self._do_stop = True
        self._stop()

    def _start(self):
        if self._do_process:
            self._processes = [
                Process(
                    name=f"process-{i+1}/{self.size}",
                    target=self._mainloop,
                )
                for i in range(self._size)
            ]
            for p in self._processes:
                p.start()

        else:
            self._threads = [
                Thread(name=f"thread-{i+1}/{self.size}", target=self._mainloop)
                for i in range(self._size)
            ]
            for t in self._threads:
                t.start()

    def _stop(self):
        if self._do_process:
            for t in self._processes:
                t.join()
        else:
            for t in self._threads:
                t.join()

    def _mainloop(self):
        while not self._do_stop:
            try:
                action = self._queue.get(timeout=1)
                if action.get("filename"):
                    try:
                        image = PIL.Image.open(action["filename"])
                        if action.get("resize"):
                            image = resize_crop(image, action["resize"])

                        self._result_queue.put_nowait({
                            "filename": action["filename"],
                            "image": image,
                        })
                    except Exception as e:
                        self._result_queue.put_nowait({
                            "filename": action["filename"],
                            "error": f"{type(e).__name__}: {e}"
                        })

                if action.get("stop"):
                    if self._verbose:
                        self._log("received stop")
                    self._do_stop = True
                    self._queue.put_nowait(action)

                self._queue.task_done()
            except queue.Empty:
                pass

    def _log(self, *args, **kwargs):
        if self._verbose:
            name = current_process().name if self._do_process else current_thread().name
            log.log(f"{name}:", *args, **kwargs)
