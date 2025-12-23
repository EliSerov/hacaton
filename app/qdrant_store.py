from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Any
from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams, Filter, FieldCondition, MatchValue, Range, Condition, PointStruct

logger = logging.getLogger(__name__)

@dataclass
class QdrantStore:
    url: str
    collection: str

    def client(self) -> QdrantClient:
        return QdrantClient(url=self.url)

    def ensure_collection(self, dim: int) -> None:
        c = self.client()
        if any(x.name == self.collection for x in c.get_collections().collections):
            return
        logger.info("Creating Qdrant collection '%s' dim=%s cosine", self.collection, dim)
        c.create_collection(collection_name=self.collection, vectors_config=VectorParams(size=dim, distance=Distance.COSINE))

    def upsert_points(self, points: list[PointStruct]) -> None:
        if points:
            self.client().upsert(collection_name=self.collection, points=points)

    def search(self, query_vector: list[float], limit: int, qfilter: Filter | None) -> list[dict[str, Any]]:
        hits = self.client().search(collection_name=self.collection, query_vector=query_vector, limit=limit, query_filter=qfilter, with_payload=True)
        return [{"score": float(h.score), "payload": (h.payload or {})} for h in hits]

def build_filter(author: str | None, topic: str | None, date_from_ts: int | None, date_to_ts: int | None) -> Filter | None:
    must: list[Condition] = []
    if author:
        must.append(FieldCondition(key="author", match=MatchValue(value=author)))
    if topic:
        must.append(FieldCondition(key="subtopic", match=MatchValue(value=topic)))
    if date_from_ts is not None or date_to_ts is not None:
        must.append(FieldCondition(key="pub_date_ts", range=Range(gte=date_from_ts, lte=date_to_ts)))
    return Filter(must=must) if must else None
