import os
from functools import partial
from pathlib import Path
import threading
from typing import Union

from src.hf import HuggingfaceSpace, SpacePool


class Client:

    _singleton = None

    @classmethod
    def singleton(cls) -> "Client":
        if cls._singleton is None:
            cls._singleton = Client()
        return cls._singleton

    def __init__(self):
        self.pool = SpacePool()
        self.pool.start()
        self.result_path = Path(__file__).resolve().parent.parent.parent.parent / "results"
        self.num_digits = 4
        self._lock = threading.Lock()
        self._spaces = []

    def stop(self):
        self.pool.stop()

    def run_space(
            self,
            space: HuggingfaceSpace,
            path: Union[str, Path],
            slug: str,
    ):
        if space in self._spaces:
            raise ValueError(f"Space {space} is already running")

        self._spaces.append(space)
        space.finished = partial(self._on_finished, space, Path(path), slug)
        self.pool.run(space)

    def status(self) -> dict:
        return {
            id(space): space.state
            for space in self._spaces
        }

    def _on_finished(self, space: HuggingfaceSpace, path: Path, slug: str):
        results = space.result()
        if results:
            for result in results:
                self._store_result(result, path, slug)
                try:
                    self._spaces.remove(space)
                except ValueError:
                    pass

    def _store_result(self, result, path: Path, filename: str) -> Path:
        with self._lock:
            full_path = self.result_path / path
            os.makedirs(full_path, exist_ok=True)

            def _get_full_name(count):
                return full_path / f"{filename}-{count:0{self.num_digits}d}.{result.extension}"

            count = 0
            full_name = _get_full_name(count)
            if full_name.exists():
                all_files = full_path.glob(f"{filename}-*.{result.extension}")
                numbers = []
                for f in all_files:
                    try:
                        numbers.append(int(f.name.split("-")[-1].split(".", 1)[0]))
                    except ValueError:
                        pass
                if numbers:
                    count = sorted(numbers)[-1]

            full_name = _get_full_name(count)
            while full_name.exists():  # some fallback
                count += 1
                full_name = _get_full_name(count)

            print(f"SAVING {full_name}")
            result.save(full_name)
            return full_name