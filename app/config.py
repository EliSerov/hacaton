from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    qdrant_url: str = Field(default="http://qdrant:6333", alias="QDRANT_URL")
    qdrant_collection: str = Field(default="articles", alias="QDRANT_COLLECTION")

    embed_model: str = Field(default="sentence-transformers/paraphrase-multilingual-MiniLM-L12-v2", alias="EMBED_MODEL")
    gen_model: str = Field(default="Qwen/Qwen2.5-1.5B-Instruct", alias="GEN_MODEL")
    device: str = Field(default="auto", alias="DEVICE")  # auto|cuda|cpu

    auto_ingest: bool = Field(default=False, alias="AUTO_INGEST")
    csv_glob: str = Field(default="/app/data/*.csv", alias="CSV_GLOB")
    chunk_size: int = Field(default=1200, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(default=200, alias="CHUNK_OVERLAP")

    top_k: int = Field(default=5, alias="TOP_K")
    api_key: str | None = Field(default=None, alias="API_KEY")

def get_settings() -> Settings:
    return Settings()
