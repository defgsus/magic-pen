import os.path
from pathlib import Path
from typing import List, Iterable, Optional

import PIL.Image
import sqlalchemy as sq
from sqlalchemy.orm import relationship, backref, sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError


ImageDBBase = declarative_base()


image_tags = sq.Table(
    "image_tags",
    ImageDBBase.metadata,
    sq.Column("image_id", sq.ForeignKey("image.id"), primary_key=True),
    sq.Column("tag_id", sq.ForeignKey("tag.id"), primary_key=True),
)


class ImageEntry(ImageDBBase):
    __tablename__ = 'image'

    id = sq.Column(sq.Integer, sq.Sequence("id_seq"), primary_key=True)
    path = sq.Column(sq.String, index=True)
    name = sq.Column(sq.String, index=True)

    tags = relationship("ImageTag", secondary=image_tags, back_populates="images")
    embeddings = relationship("Embedding", back_populates="images")

    def __repr__(self):
        return f"<{self.name}>"

    def filename(self) -> Path:
        return Path(self.path) / self.name

    def mime_type(self) -> str:
        _, ext = os.path.splitext(self.name)
        ext = ext[1:]
        if ext == "jpg":
            ext = "jpeg"
        return f"image/{ext}"

    def load_pil(self) -> PIL.Image.Image:
        return PIL.Image.open(self.filename())

    def _ipython_display_(self):
        from IPython.display import display
        display(self.load_pil())


class ImageTag(ImageDBBase):
    __tablename__ = 'tag'

    id = sq.Column(sq.Integer, sq.Sequence("id_seq"), primary_key=True)
    name = sq.Column(sq.String(32), index=True, nullable=False, unique=True)

    images = relationship("ImageEntry", secondary=image_tags, back_populates="tags")


class Embedding(ImageDBBase):
    __tablename__ = 'embedding'

    id = sq.Column(sq.Integer, sq.Sequence("id_seq"), primary_key=True)
    model = sq.Column(sq.String(16), index=True)
    #data = sq.Column(sq.ARRAY(sq.Float))
    data = sq.Column(sq.String)

    image_id = sq.Column(sq.Integer, sq.ForeignKey("image.id", ondelete="RESTRICT"), index=True)
    images = relationship("ImageEntry", back_populates="embeddings")

    sq.UniqueConstraint(model, image_id)

    def to_list(self) -> List[float]:
        return [float(i) for i in self.data.split(",")]

    def to_numpy(self, dtype="float32"):
        import numpy as np
        return np.array(self.to_list(), dtype=dtype)

    @classmethod
    def to_internal_data(cls, sequence: Iterable[float]) -> str:
        return ",".join(str(f) for f in sequence)
