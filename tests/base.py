import unittest
import tempfile
from pathlib import Path

import PIL.Image

from src.image import *


DATA_PATH = Path(__file__).resolve().parent / "data"


class TestBase(unittest.TestCase):

    def load_pil(self, fn: Union[str, Path]) -> PIL.Image.Image:
        return PIL.Image.open(DATA_PATH / fn)
