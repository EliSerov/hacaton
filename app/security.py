from __future__ import annotations
from fastapi import Header, HTTPException
from app.config import Settings

def require_api_key(settings: Settings, x_api_key: str | None = Header(default=None, alias="X-Api-Key")) -> None:
    if not settings.api_key:
        return
    if x_api_key != settings.api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
