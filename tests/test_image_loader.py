import time
from tests.base import *

from src.imagedb import *


class TestImageLoader(TestBase):

    def test_100_loader(self):

            filenames = map(str, [
                DATA_PATH / "gray48x32.png",
                DATA_PATH / "rgb48x32.png",
                DATA_PATH / "rgba48x32.png",
                DATA_PATH / "animals" / "dog-with-a-green-hat.png",
                DATA_PATH / "animals" / "dog-with-a-red-hat.png",
                DATA_PATH / "animals" / "zebra-with-a-green-hat.png",
                DATA_PATH / "animals" / "zebra-with-a-red-hat.png",
            ])

            for do_process in (False, True):
                for size in (1, 4, 20):
                    print(f"-- running size={size} do_process={do_process}")

                    start_time = time.time()
                    with ImageLoader(size=size, do_process=do_process, verbose=True) as loader:
                        images = loader.load_images(filenames, resize=(128, 96))
                    run_time = time.time() - start_time

                    print("TIME (sec):", run_time)

                    for filename in filenames:
                        self.assertIn(filename, images)
                        self.assertEqual(128, images[filename]["image"].width)
                        self.assertEqual(96, images[filename]["image"].height)
