import sqlalchemy as sq
from sqlalchemy.orm import relationship, backref, sessionmaker, Session
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.exc import IntegrityError


ImageDBBase = declarative_base()


class ContentHash(ImageDBBase):
    __tablename__ = 'content_hash'

    id = sq.Column(sq.Integer, sq.Sequence("id_seq"), primary_key=True, unique=True)
    hash = sq.Column(sq.String(length=128))
    images = relationship("ImageEntry")


class ImageEntry(ImageDBBase):
    __tablename__ = 'image'

    id = sq.Column(sq.Integer, sq.Sequence("id_seq"), primary_key=True)
    path = sq.Column(sq.String)

    content_hash_id = sq.Column(sq.Integer, sq.ForeignKey("content_hash.id", ondelete="RESTRICT"))
