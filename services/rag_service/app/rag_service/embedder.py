import numpy as np
from sentence_transformers import SentenceTransformer


class QueryEmbedder:
    def __init__(self, model_name: str) -> None:
        self._model = SentenceTransformer(model_name)

    def embed(self, query: str) -> np.ndarray:
        q = f"query: {query}"
        vec = self._model.encode([q], normalize_embeddings=True, show_progress_bar=False)[0]
        return np.asarray(vec)
