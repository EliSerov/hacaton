from __future__ import annotations
import logging
from app.logging_conf import setup_logging
from app.config import get_settings
from app.qdrant_store import QdrantStore
from app.rag import RAGEngine
from app.generator import LocalGenerator
from app.api import create_api
from app.ingest import iter_csv_files, ingest_csv_files

setup_logging()
logger = logging.getLogger(__name__)
settings = get_settings()

store = QdrantStore(url=settings.qdrant_url, collection=settings.qdrant_collection)
rag = RAGEngine(store=store, embed_model=settings.embed_model, device=settings.device, top_k=settings.top_k)
generator = LocalGenerator(model_name=settings.gen_model, device=settings.device)

app = create_api(settings=settings, rag=rag, generator=generator)

@app.on_event("startup")
def _startup():
    if settings.auto_ingest:
        try:
            paths = iter_csv_files(settings.csv_glob)
            if paths:
                logger.info("AUTO_INGEST enabled. Found %s CSV file(s). Starting ingest...", len(paths))
                ingest_csv_files(store, paths, settings.embed_model, settings.device, settings.chunk_size, settings.chunk_overlap)
            else:
                logger.info("AUTO_INGEST enabled but no CSV files found by glob: %s", settings.csv_glob)
        except Exception as e:
            logger.exception("AUTO_INGEST failed: %s", e)
