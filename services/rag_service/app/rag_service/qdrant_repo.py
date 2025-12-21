from typing import Any, Dict, List, Optional
from qdrant_client import QdrantClient
from qdrant_client.http.models import Filter, FieldCondition, MatchValue, MatchAny


class QdrantSearchRepository:
    def __init__(self, host: str, port: int, collection: str) -> None:
        self._client = QdrantClient(host=host, port=port)
        self._collection = collection

    def search(self, vector: List[float], qfilter: Optional[Filter], limit: int) -> List[Dict[str, Any]]:
        hits = self._client.search(
            collection_name=self._collection,
            query_vector=vector,
            query_filter=qfilter,
            limit=limit,
            with_payload=True,
        )
        out = []
        for h in hits:
            out.append({"score": float(h.score), "payload": h.payload or {}})
        return out


    def retrieve_vector(self, point_id: str) -> Optional[List[float]]:
        pts = self._client.retrieve(
            collection_name=self._collection,
            ids=[point_id],
            with_vectors=True,
            with_payload=False,
        )
        if not pts:
            return None
        vec = pts[0].vector
        # qdrant-client may return dict or list depending on config
        if isinstance(vec, dict):
            # take first vector
            return list(next(iter(vec.values())))
        return list(vec)

    def scroll_payloads(self, qfilter: Filter, limit: int = 10) -> List[Dict[str, Any]]:
        points, _ = self._client.scroll(
            collection_name=self._collection,
            scroll_filter=qfilter,
            limit=limit,
            with_payload=True,
            with_vectors=False,
        )
        out = []
        for p in points:
            out.append({"id": p.id, "payload": p.payload or {}})
        return out

    @staticmethod
    def build_filter(author: Optional[str], day: Optional[str], topic: Optional[str]) -> Optional[Filter]:
        must = []
        if author:
            must.append(FieldCondition(key="author_norm", match=MatchValue(value=author.strip().lower())))
        if day:
            must.append(FieldCondition(key="pub_day", match=MatchValue(value=day.strip())))
        if topic:
            must.append(FieldCondition(key="topics_norm", match=MatchAny(any=[topic.strip().lower()])))
        if not must:
            return None
        return Filter(must=must)
