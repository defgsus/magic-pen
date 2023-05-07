import json
import os
from functools import partial
from pathlib import Path
import threading
from typing import Union, Set, Dict, Optional, Callable

from src.config import RESULTS_PATH
from src.hf import HuggingfaceSpace, SpacePool


class Client:

    _singleton = None

    @classmethod
    def singleton(cls) -> "Client":
        if cls._singleton is None:
            cls._singleton = Client()
        return cls._singleton

    def __init__(self, pool_size: int = 20):
        self.pool = SpacePool(size=pool_size)
        self.pool.start()
        self.result_path = RESULTS_PATH
        self.num_digits = 4
        self._lock = threading.Lock()
        self._spaces: Set[HuggingfaceSpace] = set()
        self._space_ids: Dict[str, HuggingfaceSpace] = {}

    def stop(self):
        self.pool.stop()

    def run_space(
            self,
            space: HuggingfaceSpace,
            path: Union[str, Path],
            slug: str,
            callback: Optional[Callable] = None,
    ):
        if space in self._spaces:
            raise ValueError(f"Space {space} is already running")

        space_id = self._get_new_space_id(slug)
        self._spaces.add(space)
        self._space_ids[space_id] = space

        space.finished = partial(self._on_finished, space, Path(path), slug, space_id, callback)
        self.pool.run(space)

    def status(self) -> dict:
        return {
            space_id: space.status_str()
            for space_id, space in self._space_ids.items()
        }

    def _get_new_space_id(self, slug: str) -> str:
        space_id = slug
        count = 2
        while space_id in self._space_ids:
            space_id = f"{slug}-{count}"
            count += 1
        return space_id

    def _on_finished(
            self,
            space: HuggingfaceSpace,
            path: Path,
            slug: str,
            space_id: str,
            callback: Optional[Callable],
    ):
        results = space.result()
        if results:
            for result in results:
                self._store_result(space, result, path, slug)

        if callback:
            callback()

        try:
            self._spaces.remove(space)
        except KeyError:
            pass
        try:
            self._space_ids.pop(space_id)
        except KeyError:
            pass

    def _store_result(self, space: HuggingfaceSpace, result, path: Path, filename: str) -> Path:
        with self._lock:
            full_path = self.result_path / path
            os.makedirs(full_path, exist_ok=True)

            def _get_full_name(count: int, ext: Optional[str] = None):
                return full_path / f"{filename}-{count:0{self.num_digits}d}.{ext or result.extension}"

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

            data_name = _get_full_name(count, "json")
            data_name.write_text(json.dumps(space.parameters()))

            return full_name
