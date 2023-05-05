from tests.base import *

from src.imagedb import ImageDB


class TestImageDB(TestBase):

    def test_100_all_data(self):
        with tempfile.TemporaryDirectory() as tmp_dir:

            # -- add directory --
            db = ImageDB(tmp_dir, verbose=True)

            db.add_directory(DATA_PATH, recursive=False, tags=["tag1"])
            # make sure images are only added once
            db.add_directory(DATA_PATH, recursive=False, tags=["tag2"])

            # -- new db instance, check contents --
            db = ImageDB(tmp_dir, verbose=True)

            self.assertEqual(3, db.num_images())

            image_path = DATA_PATH / "gray48x32.png"
            with db.sql_session() as session:
                entry = db.get_image(image_path, sql_session=session)
                self.assertTrue(entry.id)

                # -- add an embedding --
                embedding = db.add_embedding(entry.content_hash, "fake", [1, 2, 3, 4], sql_session=session)
                self.assertTrue(embedding)

            # -- new db instance, check contents --
            db = ImageDB(tmp_dir, verbose=True)

            with db.sql_session() as session:
                entry = db.get_image(image_path, sql_session=session)
                embedding = db.get_embedding(entry, "fake", sql_session=session)
                self.assertTrue(embedding)
                self.assertEqual([1, 2, 3, 4], embedding.to_list())

                self.assertEqual(
                    ["tag1", "tag2"],
                    sorted(t.name for t in entry.tags)
                )
