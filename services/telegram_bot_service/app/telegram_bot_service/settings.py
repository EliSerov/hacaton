from __future__ import annotations

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    bot_token: str = Field(alias="BOT_TOKEN")

    amqp_url: str = Field(default="amqp://guest:guest@rabbitmq:5672/", alias="AMQP_URL")
    rag_exchange: str = Field(default="rag.rpc", alias="RAG_EXCHANGE")
    rag_routing_search: str = Field(default="search", alias="RAG_ROUTING_SEARCH")
    rag_routing_recommend: str = Field(default="recommend", alias="RAG_ROUTING_RECOMMEND")
    rag_routing_quiz: str = Field(default="quiz", alias="RAG_ROUTING_QUIZ")
    rag_rpc_timeout_s: float = Field(default=35.0, alias="RAG_RPC_TIMEOUT_S")

    # Optional access control (comma-separated Telegram user ids). Empty => allow everyone.
    allowed_telegram_ids: str | None = Field(default=None, alias="ALLOWED_TELEGRAM_IDS")

    # Optional shared secret used as AMQP header for service-to-service authorization
    service_api_key: str | None = Field(default=None, alias="SERVICE_API_KEY")


    def allowed_ids(self) -> set[int]:
        if not self.allowed_telegram_ids:
            return set()
        out=set()
        for part in self.allowed_telegram_ids.split(','):
            p=part.strip()
            if not p:
                continue
            try:
                out.add(int(p))
            except ValueError:
                continue
        return out


settings = Settings()
