from __future__ import annotations
import logging
from fastapi import FastAPI, Depends
from app.config import Settings
from app.models import SearchRequest, SearchResponse, ArticleOut
from app.security import require_api_key
from app.rag import RAGEngine
from app.generator import LocalGenerator

logger = logging.getLogger(__name__)

def create_api(settings: Settings, rag: RAGEngine, generator: LocalGenerator) -> FastAPI:
    app = FastAPI(title="Cloud.ru RAG MVP (local GPU models)")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    @app.post("/rag/search", response_model=SearchResponse)
    def rag_search(req: SearchRequest, _: None = Depends(lambda: require_api_key(settings))):
        results = rag.retrieve(req.query, req.author, req.date, req.topic, top_k=settings.top_k)

        if not results:
            return SearchResponse(summary="Ничего не найдено. Попробуйте изменить запрос или фильтры.", articles=[])

        contexts = []
        for r in results[: min(5, len(results))]:
            contexts.append({
                "source": {
                    "title": r["source"]["title"],
                    "author": r["source"]["author"],
                    "platform": r["source"]["platform"],
                    "pub_date": r["source"]["pub_date"],
                    "url": r["source"]["url"],
                },
                "snippets": r["snippets"][:3],
            })

        try:
            summary = generator.summarize(req.query, contexts)
        except Exception as e:
            logger.exception("Generation failed: %s", e)
            summary = "Не удалось сгенерировать саммари. Возвращаю найденные статьи."

        articles = []
        for r in results:
            s = r["source"]
            articles.append(ArticleOut(
                id=s["id"],
                title=s["title"],
                url=s["url"],
                author=s.get("author"),
                date=s.get("pub_date"),
                topic=s.get("subtopic"),
                platform=s.get("platform"),
                score=float(r["score"]),
            ))

        return SearchResponse(summary=summary, articles=articles)

    return app
