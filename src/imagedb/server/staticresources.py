from typing import Optional, Dict

from src.imagedb import ImageDB


class StaticResources:

    def __init__(self, db: ImageDB):
        self.db = db
