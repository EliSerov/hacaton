import uuid
from typing import List
from qdrant_client import QdrantClient
from qdrant_client.http.models import VectorParams, Distance, PointStruct


class QdrantRepository:
    def __init__(self, host: str, port: int, collection: str, vector_size: int) -> None:
        self._client = QdrantClient(host=host, port=port)
        self._collection = collection
        self._vector_size = vector_size

    def ensure_collection(self) -> None:
        if not self._client.collection_exists(self._collection):
            self._client.create_collection(
                collection_name=self._collection,
                vectors_config=VectorParams(size=self._vector_size, distance=Distance.COSINE),
            )

    @staticmethod
    def article_id_from_url(url: str) -> str:
        return str(uuid.uuid5(uuid.NAMESPACE_URL, url))

    def upsert(self, points: List[PointStruct]) -> None:
        self._client.upsert(collection_name=self._collection, points=points)
