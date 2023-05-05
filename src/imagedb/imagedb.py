import os
import sys
import hashlib
from pathlib import Path
from typing import Union, Optional

import sqlalchemy as sq
from sqlalchemy.orm import relationship, backref, sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError

from tqdm import tqdm
import PIL.Image

from src.image import is_image_filename
from .imagesql import ImageDBBase, ImageEntry, ContentHash


class ImageDB:

    def __init__(
            self,
            database_path: Union[str, Path],
            verbose: bool = False,
    ):
        self._database_path = Path(database_path)
        self.verbose = verbose
        self._sql_engine: Optional[sq.Engine] = None

    @property
    def database_path(self) -> Path:
        return self._database_path

    def add_image(
            self,
            path: Union[str, Path],
            sql_session: Optional[Session] = None,
    ) -> ImageEntry:
        if not isinstance(path, Path):
            path = Path(path)
        if not path.is_absolute():
            path = path.resolve()

        if not path.exists():
            raise ValueError(f"Can't add to database, file does not exist: {path}")

        if sql_session is None:
            sql_session = self.sql_session()

        content_hash = self.calc_content_hash(path)
        content_hash_entry = self.get_content_hash_entry(
            content_hash, create=True, sql_session=sql_session)

        image = ImageEntry(
            path=str(path),
            content_hash_id=content_hash_entry.id,
        )

        sql_session.add(image)
        sql_session.commit()

        if self.verbose:
            self._log(f"added image {image.id} {path}")

        return image

    def get_image(
            self,
            path: Optional[Union[str, Path]] = None,
            content_hash: Optional[Union[str, int]] = None,
            sql_session: Optional[Session] = None,
    ) -> Optional[ImageEntry]:
        if sql_session is None:
            sql_session = self.sql_session()

        query = sql_session.query(ImageEntry)
        if path is not None:
            query = query.filter(ImageEntry.path == str(path))
        if content_hash is not None:
            if isinstance(content_hash, int):
                hash_id = content_hash
            else:
                hash_entry = self.get_content_hash_entry(content_hash)
                if not hash_entry:
                    return
                hash_id = hash_entry.id
            query = query.filter(ImageEntry.content_hash_id == hash_id)

        return query.first()

    def get_content_hash_entry(
            self,
            content_hash: str = None,
            create: bool = False,
            sql_session: Optional[Session] = None,
    ) -> Optional[ContentHash]:
        if sql_session is None:
            sql_session = self.sql_session()

        query = sql_session.query(ContentHash)
        query = query.filter(ContentHash.hash == content_hash)
        entry = query.first()

        if entry is None and create:
            entry = ContentHash(hash=content_hash)
            sql_session.add(entry)
            sql_session.commit()

        return entry

    def add_directory(
            self,
            path: Union[str, Path],
            recursive: bool = False,
            sql_session: Optional[Session] = None,
    ):
        if sql_session is None:
            sql_session = self.sql_session()

        path = Path(path)
        files = path.rglob("*") if recursive else path.glob("*")
        if self.verbose:
            files = tqdm(files, desc=f"adding directory {path}")

        for file in files:
            if file.is_file() and is_image_filename(file):
                self.add_image(file, sql_session=sql_session)

    def calc_content_hash(self, path: Union[str, Path]):
        if not isinstance(path, Path):
            path = Path(path)

        return hashlib.sha512(path.read_bytes()).hexdigest()

    @property
    def sql_engine(self) -> sq.Engine:
        if self._sql_engine is None:
            os.makedirs(self._database_path, exist_ok=True)
            self._sql_engine = sq.create_engine(f"sqlite:///{self._database_path / 'db.sqlite'}")
            ImageDBBase.metadata.create_all(self._sql_engine)
        return self._sql_engine

    def sql_session(self) -> Session:
        return Session(self.sql_engine)

    def _log(self, *args, **kwargs):
        if self.verbose:
            kwargs.setdefault("file", sys.stderr)
            print("ImageDB:", *args, **kwargs)
