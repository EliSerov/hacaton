from __future__ import annotations
from pydantic import BaseModel, Field
from typing import Optional

class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1)
    author: Optional[str] = None
    date: Optional[str] = None  # YYYY-MM-DD
    topic: Optional[str] = None  # -> subtopic

class ArticleOut(BaseModel):
    id: str
    title: str
    url: str
    author: Optional[str] = None
    date: Optional[str] = None
    topic: Optional[str] = None
    platform: Optional[str] = None
    score: Optional[float] = None

class SearchResponse(BaseModel):
    summary: str
    articles: list[ArticleOut]
