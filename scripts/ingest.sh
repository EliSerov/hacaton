#!/usr/bin/env bash
set -euo pipefail
docker exec -it cloudru_rag_api python3 -c "from app.config import get_settings; from app.qdrant_store import QdrantStore; from app.ingest import iter_csv_files, ingest_csv_files; s=get_settings(); st=QdrantStore(s.qdrant_url,s.qdrant_collection); paths=iter_csv_files(s.csv_glob); print('CSV:', paths); print(ingest_csv_files(st, paths, s.embed_model, s.device, s.chunk_size, s.chunk_overlap))"
