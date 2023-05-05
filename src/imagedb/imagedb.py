import os
import hashlib
from pathlib import Path
from typing import Union, Optional, Iterable, Dict, Callable, List

import sqlalchemy as sq
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

from tqdm import tqdm
import PIL.Image

from src import log
from src.config import DATABASE_PATH
from src.image import is_image_filename
from .imagesql import ImageDBBase, ImageEntry, ContentHash, Embedding, ImageTag


class ImageDB:

    def __init__(
            self,
            database_path: Optional[Union[str, Path]] = None,
            verbose: bool = False,
    ):
        self._database_path = Path(database_path) if database_path is not None else DATABASE_PATH
        self.verbose = verbose
        self._sql_engine: Optional[sq.Engine] = None

    @property
    def database_path(self) -> Path:
        return self._database_path

    @classmethod
    def normalize_path(cls, path: Union[str, Path]) -> Path:
        if not isinstance(path, Path):
            path = Path(path)
        if not path.is_absolute():
            path = path.resolve()
        return path

    def num_images(self, sql_session: Optional[Session] = None):
        with self.sql_session(sql_session) as sql_session:
            return sql_session.query(ImageEntry).count()

    def add_image(
            self,
            path: Union[str, Path],
            no_duplicates: bool = True,
            tags: Optional[Iterable[Union[int, str, ImageTag]]] = None,
            embeddings: Optional[Dict[str, Iterable[float]]] = None,
            sql_session: Optional[Session] = None,
    ) -> ImageEntry:
        path = self.normalize_path(path)
        if not path.exists():
            raise ValueError(f"Can't add to database, file does not exist: {path}")

        with self.sql_session(sql_session) as sql_session:

            image = self.get_image(path, sql_session=sql_session) if no_duplicates else None

            content_hash = self.calc_content_hash(path)
            content_hash_entry = self.get_content_hash_entry(content_hash, create=True, sql_session=sql_session)

            if embeddings is not None:
                for model_name, sequence in embeddings.items():
                    self.add_embedding(
                        content_hash=content_hash_entry,
                        model=model_name,
                        data=sequence,
                        sql_session=sql_session,
                        commit=False,
                    )

            if image is None:
                image = ImageEntry(
                    path=str(path.parent),
                    name=path.name,
                    content_hash_id=content_hash_entry.id,
                )
                sql_session.add(image)
                sql_session.commit()

            if tags is not None:
                tags = self.get_tags(tags, sql_session=sql_session)
                for tag in tags:
                    image.tags.append(tag)

                sql_session.commit()

                #if self.verbose:
                #    self._log(f"added image {image.id} {path}")

        return image

    def add_embedding(
            self,
            content_hash: Union[int, ContentHash],
            model: str,
            data: Iterable[float],
            sql_session: Optional[Session] = None,
            commit: bool = True,
    ) -> Embedding:
        with self.sql_session(sql_session) as sql_session:

            if isinstance(content_hash, int):
                content_hash = sql_session.query(ContentHash).filter(ContentHash.id == content_hash).first()
                if not content_hash:
                    raise ValueError(f"ContentHash.id == {content_hash} does not exist")

            embedding = Embedding(
                model=model,
                data=Embedding.to_internal_data(data),
                content_hash_id=content_hash.id,
            )
            sql_session.add(embedding)
            if commit:
                sql_session.commit()

            return embedding

    def get_image(
            self,
            path: Optional[Union[str, Path]] = None,
            content_hash: Optional[Union[str, int]] = None,
            sql_session: Optional[Session] = None,
    ) -> Optional[ImageEntry]:
        with self.sql_session(sql_session) as sql_session:

            query = sql_session.query(ImageEntry)

            if path is not None:
                path = self.normalize_path(path)
                query = query.filter(ImageEntry.path == str(path.parent), ImageEntry.name == path.name)

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

    def get_embedding(
            self,
            content: Union[int, ContentHash, ImageEntry],
            model: str,
            sql_session: Optional[Session] = None,
    ) -> Optional[Embedding]:
        with self.sql_session(sql_session) as sql_session:

            if isinstance(content, int):
                content_hash_id = content

            elif isinstance(content, ContentHash):
                content_hash_id = content.id

            elif isinstance(content, ImageEntry):
                content_hash_id = content.content_hash_id

            else:
                raise TypeError(f"Expected ContentHash/id or ImageEntry, got {type(content).__name__}")

            return sql_session.query(Embedding).filter(
                Embedding.content_hash_id == content_hash_id,
                Embedding.model == model,
            ).first()

    def get_content_hash_entry(
            self,
            content_hash: str = None,
            create: bool = False,
            sql_session: Optional[Session] = None,
    ) -> Optional[ContentHash]:
        with self.sql_session(sql_session) as sql_session:

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
            glob_pattern: str = "*",
            tags: Optional[Iterable[Union[int, str, ImageTag]]] = None,
            recursive: bool = False,
            no_duplicates: bool = True,
            sql_session: Optional[Session] = None,
    ):
        with self.sql_session(sql_session) as sql_session:

            path = self.normalize_path(path)
            files = path.rglob(glob_pattern) if recursive else path.glob(glob_pattern)
            if self.verbose:
                files = tqdm(files, desc=f"adding {'recursive ' if recursive else ''}directory {path}")

            if tags is not None:
                tags = self.get_tags(tags, sql_session=sql_session)

            for file in files:
                if file.is_file() and is_image_filename(file):
                    self.add_image(
                        file,
                        tags=tags,
                        no_duplicates=no_duplicates,
                        sql_session=sql_session,
                    )

    def calc_content_hash(self, path: Union[str, Path]):
        if not isinstance(path, Path):
            path = Path(path)

        return hashlib.sha512(path.read_bytes()).hexdigest()

    @property
    def sql_engine(self) -> sq.Engine:
        if self._sql_engine is None:
            os.makedirs(self._database_path, exist_ok=True)
            self._sql_engine = sq.create_engine(
                f"sqlite:///{self._database_path / 'db.sqlite'}",
            )
            ImageDBBase.metadata.create_all(self._sql_engine)
        return self._sql_engine

    def sql_session(self, override: Optional[Session] = None) -> Session:
        if override is not None:
            class _Session:
                def __init__(self, session: Session):
                    self.session = session

                def __enter__(self):
                    return self.session

                def __exit__(self, exc_type, exc_val, exc_tb):
                    pass

            return _Session(override)

        return Session(self.sql_engine)

    def _log(self, *args, **kwargs):
        if self.verbose:
            log.log("ImageDB:", *args, **kwargs)

    def get_tags(
            self,
            tags: Iterable[Union[int, str, ImageTag]],
            sql_session: Optional[Session] = None,
    ) -> List[ImageTag]:
        with self.sql_session(sql_session) as sql_session:
            ret_list = []
            for tag in tags:
                if isinstance(tag, ImageTag):
                    tag_entry = tag
                elif isinstance(tag, int):
                    tag_entry = sql_session.query(ImageTag).filter(ImageTag.id == tag).one()
                elif isinstance(tag, str):
                    tag_entry = sql_session.query(ImageTag).filter(ImageTag.name == tag).first()
                    if not tag_entry:
                        tag_entry = ImageTag(name=tag)
                        sql_session.add(tag_entry)
                        sql_session.commit()
                else:
                    raise TypeError(f"Expected int|str|ImageTag, got '{type(tag).__name__}'")

                ret_list.append(tag_entry)

            return ret_list

    def update_embeddings(
            self,
            model: Optional[str] = None,
            device: str = "auto",
            batch_size: int = 10,
            sql_session: Optional[Session] = None,
    ):
        from src.clip import ClipSingleton, get_image_features, DEFAULT_MODEL
        model = model or DEFAULT_MODEL

        with self.sql_session(sql_session) as sql_session:
            hashes = sql_session.query(ContentHash).filter(
                ~ContentHash.embeddings.any(model=model)
            )
            total = hashes.count()
            if not total:
                if self.verbose:
                    self._log(f"no missing embeddings for model '{model}'")
                    return

            if self.verbose:
                clip_model, preproc = ClipSingleton.get(model, device)
                self._log(f"update {total} embeddings with model '{model}' on device '{clip_model.device}'")

            def _update_all(callback: Optional[Callable]):
                while True:
                    hash_entries = hashes[:batch_size]
                    if not hash_entries:
                        break

                    images = []
                    for hash_entry in hash_entries:
                        image_entry = hash_entry.images[0]

                        image = PIL.Image.open(Path(image_entry.path) / Path(image_entry.name))
                        images.append(image)

                    features = get_image_features(images, model=model, device=device)

                    embedding_entries = [
                        Embedding(
                            model=model,
                            data=Embedding.to_internal_data(feature),
                            content_hash_id=hash_entry.id,
                        )
                        for hash_entry, feature in zip(hash_entries, features)
                    ]
                    sql_session.add_all(embedding_entries)
                    sql_session.commit()

                    if callback:
                        callback(len(hash_entries))

            if self.verbose:
                with tqdm(f"update embeddings", total=total) as log:
                    _update_all(lambda n: log.update(n))
            else:
                _update_all(None)
