from tests.base import *

from src.imagedb import ImageDB


class TestImageDB(TestBase):

    def test_100_all_data(self):
        with tempfile.TemporaryDirectory() as tmp_dir:

            # -- add directory --
            db = ImageDB(tmp_dir, verbose=True)

            db.add_directory(DATA_PATH, recursive=False)

            # -- new db instance, check contents --
            db = ImageDB(tmp_dir, verbose=True)

            image_path = DATA_PATH / "gray48x32.png"
            entry = db.get_image(image_path)
            self.assertTrue(entry.id)

            