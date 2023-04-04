import unittest
from pathlib import Path

import PIL.Image

from src.image import *


DATA_PATH = Path(__file__).resolve().parent / "data"


class TestImageConv(unittest.TestCase):

    def load_pil(self, fn: Union[str, Path]) -> PIL.Image.Image:
        return PIL.Image.open(DATA_PATH / fn)

    def test_100_all_channel_types(self):
        for filename, expected_mode, expected_channels, expected_width, expected_height in (
                ("gray48x32.png", "L", 1, 48, 32),
                ("rgb48x32.png", "RGB", 3, 48, 32),
                ("rgba48x32.png", "RGBA", 4, 48, 32),
        ):
            for image_to_X in (image_to_numpy, image_to_torch):
                try:
                    pil_image = self.load_pil(filename)
                    self.assertEqual(expected_mode, pil_image.mode)
                    self.assertEqual(expected_width, pil_image.width)
                    self.assertEqual(expected_height, pil_image.height)

                    np_image = image_to_X(pil_image)
                    self.assertEqual((expected_channels, expected_height, expected_width), np_image.shape)

                    pil_image_2 = image_to_pil(np_image)
                    self.assertEqual(expected_mode, pil_image_2.mode)
                    self.assertEqual(expected_width, pil_image_2.width)
                    self.assertEqual(expected_height, pil_image_2.height)

                    self.assertEqual(pil_image.tobytes(), pil_image_2.tobytes())

                except Exception as e:
                    print(f"\nIN {filename}:\n")
                    raise
