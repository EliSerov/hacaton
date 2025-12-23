from __future__ import annotations
import glob, logging, zlib
import pandas as pd
from dateutil import parser as dateparser
from qdrant_client.http.models import PointStruct
from app.chunking import chunk_text
from app.embeddings import get_embedder
from app.qdrant_store import QdrantStore

logger = logging.getLogger(__name__)
REQUIRED_COLS = {"id","title","author","platform","url","content","pub_date","subtopic"}

def stable_point_id(source_id: str) -> int:
    return int(source_id) if source_id.isdigit() else int(zlib.adler32(source_id.encode("utf-8")))

def parse_pub_date_ts(pub_date: str | None) -> int | None:
    if not pub_date or str(pub_date).strip() == "":
        return None
    try:
        dt = dateparser.parse(str(pub_date))
        return int(dt.timestamp()) if dt else None
    except Exception:
        return None

def iter_csv_files(csv_glob: str) -> list[str]:
    return sorted(glob.glob(csv_glob))

def ingest_csv_files(store: QdrantStore, csv_paths: list[str], embed_model: str, device: str, chunk_size: int, chunk_overlap: int, batch_size: int = 64) -> dict:
    emb = get_embedder(embed_model, device)
    store.ensure_collection(emb.dim)

    total_points = 0
    total_articles = 0

    for path in csv_paths:
        logger.info("Reading CSV: %s", path)
        df = pd.read_csv(path, sep=",", encoding="utf-8")
        missing = REQUIRED_COLS - set(df.columns)
        if missing:
            raise ValueError(f"CSV missing columns: {sorted(missing)} in {path}")

        points: list[PointStruct] = []
        texts: list[str] = []

        for _, row in df.iterrows():
            article_id = str(row.get("id","")).strip()
            if not article_id:
                continue

            title = str(row.get("title","") or "").strip()
            author = str(row.get("author","") or "").strip()
            platform = str(row.get("platform","") or "").strip()
            url = str(row.get("url","") or "").strip()
            content = str(row.get("content","") or "")
            pub_date = str(row.get("pub_date","") or "").strip()
            subtopic = str(row.get("subtopic","") or "").strip()
            pub_date_ts = parse_pub_date_ts(pub_date)

            chunks = chunk_text(content, chunk_size, chunk_overlap)
            if not chunks:
                continue
            total_articles += 1

            for ch in chunks:
                payload = {
                    "article_id": article_id,
                    "title": title,
                    "author": author,
                    "platform": platform,
                    "url": url,
                    "pub_date": pub_date,
                    "pub_date_ts": pub_date_ts,
                    "subtopic": subtopic,
                    "chunk_index": ch.index,
                    "text": ch.text,
                }
                pid = stable_point_id(f"{article_id}#{ch.index}")
                texts.append(ch.text)
                points.append(PointStruct(id=pid, vector=[], payload=payload))

                if len(points) >= batch_size:
                    vecs = emb.embed(texts)
                    for p, v in zip(points, vecs):
                        p.vector = v
                    store.upsert_points(points)
                    total_points += len(points)
                    points, texts = [], []

        if points:
            vecs = emb.embed(texts)
            for p, v in zip(points, vecs):
                p.vector = v
            store.upsert_points(points)
            total_points += len(points)

    logger.info("Ingest complete: articles=%s points=%s", total_articles, total_points)
    return {"articles": total_articles, "points": total_points}
