import logging
import uuid
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from qdrant_client.http.models import Filter, FieldCondition, MatchValue
from rag_service.domain import RetrievedChunk, AggregatedArticle

from common.contracts.models import RagRequest
from rag_service.embedder import QueryEmbedder
from rag_service.qdrant_repo import QdrantSearchRepository
from rag_service.retriever import Retriever
from rag_service.prompt_builder import PromptBuilder
from rag_service.llm import LLM
from rag_service.mapper import ContractMapper


logger = logging.getLogger(__name__)


class RecommendRequest(BaseModel):
    url: str = Field(..., min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class QuizRequest(BaseModel):
    urls: List[str] = Field(default_factory=list, min_length=1)
    n_questions: int = Field(default=8, ge=1, le=20)


class RagService:
    def __init__(
        self,
        embedder: QueryEmbedder,
        qrepo: QdrantSearchRepository,
        retriever: Retriever,
        llm: LLM,
        prompt_builder: PromptBuilder,
        mapper: ContractMapper,
    ) -> None:
        self._embedder = embedder
        self._qrepo = qrepo
        self._retriever = retriever
        self._llm = llm
        self._prompt_builder = prompt_builder
        self._mapper = mapper

    def _build_sources(self, aggregated, limit_articles: int) -> tuple[list[dict], list[dict]]:
        articles_for_contract: List[Dict[str, Any]] = []
        sources_for_llm: List[Dict[str, Any]] = []
        for art in aggregated[:limit_articles]:
            p = art.payload
            title = p.get("title", "")
            url = p.get("url", "")
            author = p.get("author", "")
            date = p.get("pub_day", "")  # contract expects YYYY-MM-DD
            topic = p.get("subtopic_raw", "")

            articles_for_contract.append({
                "title": title,
                "url": url,
                "author": author,
                "date": date,
                "topic": topic,
            })

            excerpt = "\n---\n".join([t for t in art.texts if t][:3])
            sources_for_llm.append({
                "title": title,
                "url": url,
                "author": author,
                "date": date,
                "topic": topic,
                "excerpt": excerpt,
            })
        return articles_for_contract, sources_for_llm

    def search(self, payload: Dict[str, Any], trace_id: str = "") -> Dict[str, Any]:
        try:
            req = RagRequest.model_validate(payload)
        except Exception as e:
            logger.warning("Validation error", extra={"trace_id": trace_id, "err": str(e)})
            return {"summary": "Некорректный запрос.", "articles": []}

        author = req.filters.author
        day = req.filters.date
        topic = req.filters.topic

        qfilter = self._qrepo.build_filter(author, day, topic)
        qvec = self._embedder.embed(req.query).tolist()

        chunks = self._retriever.retrieve_chunks(qvec, qfilter, limit_chunks=50)
        aggregated = self._retriever.aggregate(chunks, max_articles=5)

        if not aggregated:
            return {"summary": "Ничего не найдено по заданным фильтрам.", "articles": []}

        articles, sources = self._build_sources(aggregated, limit_articles=5)

        prompt = self._prompt_builder.build_summary(req.query, sources)
        summary = self._llm.generate(prompt).strip()
        if not summary:
            summary = f"Найдено {len(articles)} статей по запросу «{req.query}»."

        if "Источники" not in summary:
            refs = "".join([f"[{i}]" for i in range(1, len(articles) + 1)])
            summary = summary + f"\nИсточники: {refs}"

        return self._mapper.to_contract(summary, articles)

    def recommend(self, payload: Dict[str, Any], trace_id: str = "") -> Dict[str, Any]:
        """Recommend similar publications for a given seed URL.

        Payload contract:
          {"url": "<seed_url>", "top_k": 5}
        """
        try:
            req = RecommendRequest.model_validate(payload)
        except Exception:
            return {"summary": "Некорректный запрос.", "articles": []}

        seed_url = req.url.strip()
        seed_article_id = str(uuid.uuid5(uuid.NAMESPACE_URL, seed_url))

        seed_vec = self._qrepo.retrieve_vector(seed_article_id)
        if seed_vec is None:
            qf = Filter(must=[FieldCondition(key="article_id", match=MatchValue(value=seed_article_id))])
            pts = self._qrepo.scroll_payloads(qf, limit=1)
            if pts:
                seed_vec = self._qrepo.retrieve_vector(str(pts[0]["id"]))

        if seed_vec is None:
            return {"summary": "Не удалось найти исходную статью для рекомендаций.", "articles": []}

        hits = self._qrepo.search(seed_vec, qfilter=None, limit=req.top_k * 20)
        chunks = [RetrievedChunk(score=h["score"], payload=h["payload"]) for h in hits]
        aggregated = self._retriever.aggregate(chunks, max_articles=req.top_k + 5)

        aggregated = [a for a in aggregated if a.payload.get("article_id") != seed_article_id]
        if not aggregated:
            return {"summary": "Похожие публикации не найдены.", "articles": []}

        articles, _ = self._build_sources(aggregated, limit_articles=req.top_k)
        if not articles:
            return {"summary": "Похожие публикации не найдены.", "articles": []}

        refs = "".join([f"[{i}]" for i in range(1, len(articles) + 1)])
        summary = f"Найдено {len(articles)} похожих публикаций. Источники: {refs}"
        return self._mapper.to_contract(summary, articles)

    def quiz(self, payload: Dict[str, Any], trace_id: str = "") -> Dict[str, Any]:
        """Generate a quiz from a list of article URLs.

        Payload contract:
          {"urls": ["..."], "n_questions": 8}
        """
        try:
            req = QuizRequest.model_validate(payload)
        except Exception:
            return {"summary": "Некорректный запрос.", "articles": []}

        aggregated: List[AggregatedArticle] = []

        for url in req.urls:
            url = (url or "").strip()
            if not url:
                continue
            article_id = str(uuid.uuid5(uuid.NAMESPACE_URL, url))
            qf = Filter(must=[FieldCondition(key="article_id", match=MatchValue(value=article_id))])
            pts = self._qrepo.scroll_payloads(qf, limit=8)
            if not pts:
                continue

            pts_sorted = sorted(pts, key=lambda p: int(p["payload"].get("chunk_id", 0)))
            p0 = pts_sorted[0]["payload"]
            texts = []
            for p in pts_sorted[:3]:
                t = (p["payload"].get("text") or "").strip()
                if t:
                    texts.append(t)

            aggregated.append(AggregatedArticle(best_score=1.0, payload=p0, texts=texts))

        if not aggregated:
            return {"summary": "Ничего не найдено для генерации теста.", "articles": []}

        articles, sources = self._build_sources(aggregated, limit_articles=min(len(aggregated), 5))
        prompt = self._prompt_builder.build_quiz("Тест по выбранным материалам", sources, n_questions=req.n_questions)
        quiz_text = self._llm.generate(prompt).strip()

        if not quiz_text:
            quiz_text = "Тест не удалось сгенерировать на основе найденных материалов."

        if "Источники" not in quiz_text:
            refs = "".join([f"[{i}]" for i in range(1, len(articles) + 1)])
            quiz_text = quiz_text + f"Источники: {refs}"

        return self._mapper.to_contract(quiz_text, articles)

