from __future__ import annotations
import logging
from functools import lru_cache
import torch
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

def resolve_device(device: str) -> str:
    device = (device or "auto").lower()
    if device == "cuda":
        return "cuda" if torch.cuda.is_available() else "cpu"
    if device == "cpu":
        return "cpu"
    return "cuda" if torch.cuda.is_available() else "cpu"

class Embedder:
    def __init__(self, model_name: str, device: str):
        self.device = resolve_device(device)
        self.model_name = model_name
        logger.info("Loading embed model: %s (device=%s)", model_name, self.device)
        self.model = SentenceTransformer(model_name, device=self.device)

    @property
    def dim(self) -> int:
        return int(self.model.get_sentence_embedding_dimension())

    def embed(self, texts: list[str], batch_size: int = 32) -> list[list[float]]:
        embs = self.model.encode(texts, batch_size=batch_size, normalize_embeddings=True, show_progress_bar=False)
        return [e.tolist() for e in embs]

@lru_cache(maxsize=1)
def get_embedder(model_name: str, device: str) -> Embedder:
    return Embedder(model_name, device)
