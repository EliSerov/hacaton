from typing import List
import numpy as np
from sentence_transformers import SentenceTransformer


class Embedder:
    def __init__(self, model_name: str, batch_size: int) -> None:
        self._model = SentenceTransformer(model_name)
        self._batch_size = batch_size

    def embed_passages(self, passages: List[str]) -> np.ndarray:
        texts = [f"passage: {p}" for p in passages]
        vecs = self._model.encode(
            texts,
            normalize_embeddings=True,
            batch_size=self._batch_size,
            show_progress_bar=False,
        )
        return np.asarray(vecs)

    def vector_size(self) -> int:
        v = self.embed_passages(["test"])
        return int(v.shape[1])
