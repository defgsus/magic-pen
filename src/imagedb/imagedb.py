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
from src.image import is_image_filename, resize_crop
from .imagesql import ImageDBBase, ImageEntry, Embedding, ImageTag
from .simindex import SimIndex


class ImageDB:

    def __init__(
            self,
            database_path: Optional[Union[str, Path]] = None,
            verbose: bool = False,
    ):
        self._database_path = Path(database_path) if database_path is not None else DATABASE_PATH
        self.verbose = verbose
        self._sql_engine: Optional[sq.Engine] = None
        self._model_indices: Dict[str, SimIndex] = {}

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

            image = self.get_image(path=path, sql_session=sql_session) if no_duplicates else None

            if embeddings is not None:
                for model_name, sequence in embeddings.items():
                    self.add_embedding(
                        image_or_id=image,
                        model=model_name,
                        data=sequence,
                        sql_session=sql_session,
                        commit=False,
                    )

            do_commit = False

            if image is None:
                image = ImageEntry(
                    path=str(path.parent),
                    name=path.name,
                )
                sql_session.add(image)
                do_commit = True

            if tags is not None:
                tags = self.get_tags(tags, sql_session=sql_session)
                for tag in tags:
                    image.tags.append(tag)

                do_commit = True

            if do_commit:
                sql_session.commit()

        return image

    def add_embedding(
            self,
            image_or_id: Union[int, ImageEntry],
            model: str,
            data: Iterable[float],
            sql_session: Optional[Session] = None,
            commit: bool = True,
    ) -> Embedding:
        with self.sql_session(sql_session) as sql_session:

            if isinstance(image_or_id, int):
                image = sql_session.query(ImageEntry).filter(ImageEntry.id == image_or_id).first()
                if not image:
                    raise ValueError(f"ContentHash.id == {image_or_id} does not exist")
            else:
                image = image_or_id

            embedding = Embedding(
                model=model,
                data=Embedding.to_internal_data(data),
                image_id=image.id,
            )
            sql_session.add(embedding)
            if commit:
                sql_session.commit()

            return embedding

    def get_image(
            self,
            id: Optional[int] = None,
            path: Optional[Union[str, Path]] = None,
            sql_session: Optional[Session] = None,
    ) -> Optional[ImageEntry]:
        with self.sql_session(sql_session) as sql_session:

            query = sql_session.query(ImageEntry)

            if id is not None:
                query = query.filter(ImageEntry.id == id)

            if path is not None:
                path = self.normalize_path(path)
                query = query.filter(ImageEntry.path == str(path.parent), ImageEntry.name == path.name)

            return query.first()

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
        from src.config import DEFAULT_CLIP_MODEL
        from src.clip import ClipSingleton, get_image_features
        model = model or DEFAULT_CLIP_MODEL

        with self.sql_session(sql_session) as sql_session:
            images = sql_session.query(ImageEntry).filter(
                ~ImageEntry.embeddings.any(model=model)
            )
            total = images.count()
            if not total:
                if self.verbose:
                    self._log(f"no missing embeddings for model '{model}'")
                    return

            if self.verbose:
                clip_model, preproc = ClipSingleton.get(model, device)
                self._log(f"update {total} embeddings with model '{model}' on device '{clip_model.device}'")

            def _update_all(callback: Optional[Callable]):
                while True:
                    image_batch = images[:batch_size]
                    if not image_batch:
                        break

                    pil_images = []
                    image_ids = []
                    for image_entry in image_batch:
                        try:
                            image = PIL.Image.open(image_entry.filename())
                            image = resize_crop(image, [224, 224])
                            pil_images.append(image)
                            image_ids.append(image_entry.id)
                        except Exception as e:
                            log.warn(f"failed loading image: {image_entry.filename()}: {type(e).__name__}: {e}")
                            sql_session.delete(image_entry)

                    features = get_image_features(pil_images, model=model, device=device)

                    embedding_entries = [
                        Embedding(
                            model=model,
                            data=Embedding.to_internal_data(feature),
                            image_id=image_id,
                        )
                        for image_id, feature in zip(image_ids, features)
                    ]
                    sql_session.add_all(embedding_entries)
                    sql_session.commit()

                    if callback:
                        callback(len(image_batch))

            if self.verbose:
                with tqdm(f"update embeddings", total=total) as progress:
                    _update_all(lambda n: progress.update(n))
            else:
                _update_all(None)

    def get_embedding(
            self,
            image_or_id: Union[int, ImageEntry],
            model: str,
            sql_session: Optional[Session] = None,
    ) -> Optional[Embedding]:
        if isinstance(image_or_id, int):
            image_id = image_or_id
        else:
            image_id = image_or_id.id

        with self.sql_session(sql_session) as sql_session:
            return sql_session.query(Embedding).filter(
                Embedding.image_id == image_id,
                Embedding.model == model,
            ).first()

    def sim_index(
            self,
            model: Optional[str] = None,
    ) -> SimIndex:
        if model not in self._model_indices:
            self._model_indices[model] = SimIndex(db=self, model=model)

        return self._model_indices[model]

    def status(self, sql_session: Optional[Session] = None) -> dict:
        with self.sql_session(sql_session) as session:
            num_tags = session.query(ImageTag).count()
            num_images = session.query(ImageEntry).count()
            num_embeddings = (
                session
                    .query(Embedding, sq.func.count(Embedding.model))
                    .group_by(Embedding.model).all()
            )
            return {
                "num_tags": num_tags,
                "num_images": num_images,
                "embeddings": [
                    {"model": e[0].model, "count": e[1]}
                    for e in sorted(num_embeddings, key=lambda e: e[0].model)
                ]
            }
