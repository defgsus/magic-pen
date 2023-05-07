import unittest
import tempfile
import time
from pathlib import Path

from src.hf import HuggingfaceSpace, ImageResult
from src.app.qgenerator.client import Client


class FakeSpace(HuggingfaceSpace):

    def __init__(self):
        super().__init__("ws://")

    def run(self):
        # print(f"running {self}")
        if self.finished is not None:
            self.finished()

    def result(self):
        return [ImageResult(data=b"123", mime_type="image/fake")]


class TestClient(unittest.TestCase):

    def test_client(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            client = Client()
            try:
                client.result_path = Path(temp_dir)

                full_path = client.result_path / "unit-tests"
                self.assertFalse(full_path.exists())

                client.run_space(FakeSpace(), path="unit-tests", slug="sluggy")
                client.run_space(FakeSpace(), path="unit-tests", slug="sluggy")
                client.run_space(FakeSpace(), path="unit-tests", slug="sluggy")
                time.sleep(.5)

                self.assertEqual(
                    ["sluggy-0000.fake", "sluggy-0001.fake", "sluggy-0002.fake"],
                    sorted(p.name for p in full_path.glob("*"))
                )

            finally:
                client.stop()
