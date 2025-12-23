from __future__ import annotations
import logging
from dataclasses import dataclass
from typing import Any
from dateutil import parser as dateparser
from app.embeddings import get_embedder
from app.qdrant_store import QdrantStore, build_filter

logger = logging.getLogger(__name__)

def date_to_day_range_ts(date_str: str | None) -> tuple[int | None, int | None]:
    if not date_str:
        return None, None
    try:
        dt = dateparser.parse(date_str)
        if not dt:
            return None, None
        start = int(dt.replace(hour=0, minute=0, second=0, microsecond=0).timestamp())
        end = int(dt.replace(hour=23, minute=59, second=59, microsecond=0).timestamp())
        return start, end
    except Exception:
        return None, None

@dataclass
class RAGEngine:
    store: QdrantStore
    embed_model: str
    device: str
    top_k: int

    def retrieve(self, query: str, author: str | None, date: str | None, topic: str | None, top_k: int | None = None) -> list[dict[str, Any]]:
        top_k = top_k or self.top_k
        emb = get_embedder(self.embed_model, self.device)
        qvec = emb.embed([query])[0]

        df, dt = date_to_day_range_ts(date)
        qfilter = build_filter(author=author, topic=topic, date_from_ts=df, date_to_ts=dt)

        hits = self.store.search(query_vector=qvec, limit=top_k, qfilter=qfilter)

        grouped: dict[str, dict[str, Any]] = {}
        for h in hits:
            p = h["payload"]
            aid = str(p.get("article_id",""))
            if not aid:
                continue
            if aid not in grouped:
                grouped[aid] = {
                    "score": h["score"],
                    "source": {
                        "id": aid,
                        "title": p.get("title","") or "",
                        "author": p.get("author","") or "",
                        "platform": p.get("platform","") or "",
                        "url": p.get("url","") or "",
                        "pub_date": p.get("pub_date","") or "",
                        "subtopic": p.get("subtopic","") or "",
                    },
                    "snippets": [],
                }
            grouped[aid]["snippets"].append((p.get("text","") or "")[:400])

        return sorted(grouped.values(), key=lambda x: x["score"], reverse=True)
