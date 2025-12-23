from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class BotSettings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    bot_token: str = Field(..., alias="BOT_TOKEN")
    rag_api_url: str = Field(default="http://api:8000", alias="RAG_API_URL")
    api_key: str | None = Field(default=None, alias="API_KEY")
    allowed_user_ids: str | None = Field(default=None, alias="ALLOWED_USER_IDS")

def get_bot_settings() -> BotSettings:
    return BotSettings()
