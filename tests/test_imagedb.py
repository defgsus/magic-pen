from tests.base import *

from src.imagedb import *


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
                entry = db.get_image(path=image_path, sql_session=session)
                self.assertTrue(entry.id)

                # -- add an embedding --
                embedding = db.add_embedding(entry, "fake", [1, 2, 3, 4], sql_session=session)
                self.assertTrue(embedding)

            # -- new db instance, check contents --
            db = ImageDB(tmp_dir, verbose=True)

            with db.sql_session() as session:
                entry = db.get_image(path=image_path, sql_session=session)
                embedding = db.get_embedding(entry, "fake")
                self.assertTrue(embedding)
                self.assertEqual([1, 2, 3, 4], embedding.to_list())

                self.assertEqual(
                    ["tag1", "tag2"],
                    sorted(t.name for t in entry.tags)
                )

    def test_500_sim_index(self):
        with tempfile.TemporaryDirectory() as tmp_dir:

            # -- add directory --
            db = ImageDB(tmp_dir, verbose=True)

            db.add_directory(DATA_PATH / "animals")
            db.update_embeddings()

            index = SimIndex(db, verbose=True)

            result = index.images_by_text("zebra with a red head", count=4)
            self.assertEqual(
                [
                    "zebra-with-a-red-hat.jpg", "zebra-with-a-green-hat.jpg",
                    "dog-with-a-red-hat.jpg", "dog-with-a-green-hat.jpg",
                ],
                [r[0].name for r in result]
            )
