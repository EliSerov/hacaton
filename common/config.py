from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field
from typing import Optional, List


class AppSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    # Security
    service_api_key: str = Field(..., alias="SERVICE_API_KEY")
    allowed_telegram_ids: str = Field("", alias="ALLOWED_TELEGRAM_IDS")  # comma-separated

    # RabbitMQ
    amqp_url: str = Field(..., alias="AMQP_URL")
    rag_rpc_exchange: str = Field("rag.rpc", alias="RAG_RPC_EXCHANGE")
    rag_search_routing_key: str = Field("search", alias="RAG_SEARCH_ROUTING_KEY")
    rag_recommend_routing_key: str = Field("recommend", alias="RAG_RECOMMEND_ROUTING_KEY")
    rag_quiz_routing_key: str = Field("quiz", alias="RAG_QUIZ_ROUTING_KEY")

    # Qdrant
    qdrant_host: str = Field("qdrant", alias="QDRANT_HOST")
    qdrant_port: int = Field(6333, alias="QDRANT_PORT")
    qdrant_collection: str = Field("tech_media_chunks", alias="QDRANT_COLLECTION")

    # Embeddings
    embed_model: str = Field("intfloat/multilingual-e5-small", alias="EMBED_MODEL")
    embed_batch_size: int = Field(32, alias="EMBED_BATCH_SIZE")

    # LLM
    llm_model_path: str = Field("/models/model.gguf", alias="LLM_MODEL_PATH")
    llm_n_ctx: int = Field(4096, alias="LLM_N_CTX")
    llm_max_tokens: int = Field(400, alias="LLM_MAX_TOKENS")
    llm_temperature: float = Field(0.2, alias="LLM_TEMPERATURE")
    llm_top_p: float = Field(0.95, alias="LLM_TOP_P")
    llm_n_gpu_layers: int = Field(35, alias="LLM_N_GPU_LAYERS")

    # Indexer
    csv_input_dir: str = Field("/data", alias="CSV_INPUT_DIR")
    chunk_size: int = Field(900, alias="CHUNK_SIZE")
    chunk_overlap: int = Field(150, alias="CHUNK_OVERLAP")
    upsert_batch_size: int = Field(256, alias="UPSERT_BATCH_SIZE")

    # Telegram
    telegram_bot_token: str = Field("CHANGE_ME", alias="TELEGRAM_BOT_TOKEN")

    # Logging
    log_level: str = Field("INFO", alias="LOG_LEVEL")

    def allowed_ids_list(self) -> List[int]:
        if not self.allowed_telegram_ids.strip():
            return []
        out = []
        for part in self.allowed_telegram_ids.split(","):
            part = part.strip()
            if part:
                try:
                    out.append(int(part))
                except ValueError:
                    continue
        return out
