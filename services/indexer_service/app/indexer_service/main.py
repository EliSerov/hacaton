"""Indexer entrypoint.

We intentionally make the entrypoint resilient to Python path differences inside
containers by ensuring the project root ("/app") is on sys.path.
"""

import os
import sys

_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

import logging
from typing import List

from qdrant_client.http.models import PointStruct

from common.config import AppSettings
from common.logging import setup_logging

from indexer_service.csv_loader import CsvDirectoryLoader
from indexer_service.normalizer import norm_text, norm_key, parse_topics, to_pub_day
from indexer_service.chunker import SimpleChunker
from indexer_service.embedder import Embedder
from indexer_service.qdrant_repo import QdrantRepository


logger = logging.getLogger(__name__)


def run() -> None:
    settings = AppSettings()
    setup_logging(settings.log_level)

    loader = CsvDirectoryLoader(settings.csv_input_dir)
    embedder = Embedder(settings.embed_model, settings.embed_batch_size)

    repo = QdrantRepository(
        host=settings.qdrant_host,
        port=settings.qdrant_port,
        collection=settings.qdrant_collection,
        vector_size=embedder.vector_size(),
    )
    repo.ensure_collection()

    chunker = SimpleChunker(chunk_size=settings.chunk_size, overlap=settings.chunk_overlap)

    batch_texts: List[str] = []
    batch_points: List[PointStruct] = []

    def flush() -> None:
        nonlocal batch_texts, batch_points
        if not batch_texts:
            return
        vecs = embedder.embed_passages(batch_texts)
        for i, p in enumerate(batch_points):
            p.vector = vecs[i].tolist()
        repo.upsert(batch_points)
        logger.info("Upserted batch", extra={"trace_id": "", "count": len(batch_points)})
        batch_texts, batch_points = [], []

    count_articles = 0
    count_chunks = 0

    for art in loader.iter_articles():
        title = norm_text(art.title)
        author = norm_text(art.author)
        platform = norm_text(art.platform)
        url = norm_text(art.url)
        content = norm_text(art.content)
        pub_date = norm_text(art.pub_date)
        subtopic = art.subtopic or ""

        if not url or not content:
            continue

        try:
            day = to_pub_day(pub_date)
        except Exception:
            # fallback: take first 10 chars if looks like YYYY-MM-DD
            day = pub_date[:10] if len(pub_date) >= 10 else ""

        article_id = repo.article_id_from_url(url)
        topics, topics_norm, subtopic_raw = parse_topics(subtopic)

        chunks = chunker.split(content)
        for chunk_id, chunk_text in enumerate(chunks):
            point_id = repo.article_id_from_url(url)
            payload = {
                "article_id": article_id,
                "title": title,
                "author": author,
                "author_norm": norm_key(author),
                "platform": platform,
                "url": url,
                "pub_date": pub_date,
                "pub_day": day,
                "topics": topics,
                "topics_norm": topics_norm,
                "subtopic_raw": subtopic_raw,
                "chunk_id": chunk_id,
                "text": chunk_text,
            }
            batch_texts.append(chunk_text)
            batch_points.append(PointStruct(id=point_id, vector=[], payload=payload))
            count_chunks += 1

            if len(batch_texts) >= settings.upsert_batch_size:
                flush()

        count_articles += 1
        if count_articles % 200 == 0:
            logger.info("Progress", extra={"trace_id": "", "articles": count_articles, "chunks": count_chunks})

    flush()
    logger.info("Indexing completed", extra={"trace_id": "", "articles": count_articles, "chunks": count_chunks})


if __name__ == "__main__":
    run()
