from typing import Any, Dict, List
from rag_service.domain import RetrievedChunk, AggregatedArticle


class Retriever:
    def __init__(self, repo) -> None:
        self._repo = repo

    def retrieve_chunks(self, query_vec: List[float], qfilter, limit_chunks: int) -> List[RetrievedChunk]:
        hits = self._repo.search(query_vec, qfilter, limit=limit_chunks)
        return [RetrievedChunk(score=h["score"], payload=h["payload"]) for h in hits]

    def aggregate(self, chunks: List[RetrievedChunk], max_articles: int, max_texts_per_article: int = 3) -> List[AggregatedArticle]:
        by_article: Dict[str, Dict[str, Any]] = {}
        for ch in chunks:
            p = ch.payload
            aid = p.get("article_id")
            if not aid:
                continue
            item = by_article.get(aid)
            if item is None:
                by_article[aid] = {
                    "best_score": ch.score,
                    "payload": p,
                    "texts": [p.get("text", "")] if p.get("text") else [],
                }
            else:
                item["best_score"] = max(item["best_score"], ch.score)
                if p.get("text") and len(item["texts"]) < max_texts_per_article:
                    item["texts"].append(p.get("text"))

        aggregated = [
            AggregatedArticle(best_score=v["best_score"], payload=v["payload"], texts=v["texts"])
            for v in by_article.values()
        ]
        aggregated.sort(key=lambda a: a.best_score, reverse=True)
        return aggregated[:max_articles]
