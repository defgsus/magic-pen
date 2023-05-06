from typing import List, Iterable, Optional, Tuple

import sqlalchemy as sq
from sqlalchemy.orm import Session
import numpy as np
import faiss
from tqdm import tqdm

from src.clip import DEFAULT_MODEL, MODEL_DIMENSIONS, get_text_features, get_image_features
from .imagesql import ImageEntry, Embedding
from .imagedb import ImageDB


class SimIndex:

    def __init__(
            self,
            db: ImageDB,
            model: Optional[str] = None,
            verbose: bool = False
    ):
        self.db = db
        self.model = model or DEFAULT_MODEL
        self.verbose = verbose
        self.dimensions = MODEL_DIMENSIONS[self.model]
        self._index_to_embedding_pk = []
        self._index_to_image_pk = []
        self._index = faiss.IndexFlatIP(self.dimensions)
        self._create()

    def _create(self, batch_size: int = 100):
        with self.db.sql_session() as sql_session:
            qset = (
                sql_session
                    .query(Embedding)
                    .filter(Embedding.model == self.model)
                    .order_by("id")
            )
            total = qset.count()

            iterable = range((total + batch_size - 1) // batch_size)
            if self.verbose:
                iterable = tqdm(iterable, desc="building faiss index")

            for i in iterable:
                embedding_entries = qset[i * batch_size: (i + 1) * batch_size]
                embeddings = []
                for e in embedding_entries:
                    embeddings.append(e.to_numpy().reshape(1, -1))
                    self._index_to_embedding_pk.append(e.id)
                    self._index_to_image_pk.append(e.content_hash.images[0].id)

                embeddings = np.concatenate(embeddings, axis=0)
                self._index.add(embeddings)

    def images_by_text(
            self,
            prompt: str,
            # negative_prompt: Optional[Iterable[str]] = None,
            count: int = 1,
            device: str = "auto",
            sql_session: Optional[Session] = None
    ) -> List[Tuple[ImageEntry, float]]:

        feature = get_text_features(text=[prompt], model=self.model, device=device)

        distances, labels = self._index.search(feature, count)

        #combined = [
        #    (d, l)
        #    for d, l in zip(distances[0], labels[0])
        #]
        #combined = sorted(combined, key=lambda d, l: d, reverse=True)

        with self.db.sql_session(sql_session) as sql_session:
            return [
                (self.db.get_image(id=self._index_to_image_pk[l], sql_session=sql_session), d)
                for d, l in zip(distances[0], labels[0])
                if l >= 0
            ]
