from __future__ import annotations
import httpx
from typing import Any

class RAGClient:
    def __init__(self, base_url: str, api_key: str | None = None, timeout: float = 30.0):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.timeout = timeout

    async def search(self, query: str, author: str | None = None, date: str | None = None, topic: str | None = None) -> dict[str, Any]:
        url = f"{self.base_url}/rag/search"
        headers = {}
        if self.api_key:
            headers["X-Api-Key"] = self.api_key
        payload = {"query": query, "author": author, "date": date, "topic": topic}
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            r = await client.post(url, json=payload, headers=headers)
            r.raise_for_status()
            return r.json()
