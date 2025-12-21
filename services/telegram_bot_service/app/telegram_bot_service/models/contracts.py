from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field


class SearchFilters(BaseModel):
    author: Optional[str] = None
    date: Optional[str] = None  # YYYY-MM-DD
    topic: Optional[str] = None


class SearchRequest(BaseModel):
    query: str = Field(min_length=1)
    filters: SearchFilters = Field(default_factory=SearchFilters)


class ArticleItem(BaseModel):
    title: str
    url: str
    author: str
    date: str
    topic: str


class SearchResponse(BaseModel):
    summary: str
    articles: List[ArticleItem] = Field(default_factory=list)


class RecommendRequest(BaseModel):
    url: str = Field(min_length=1)
    top_k: int = Field(default=5, ge=1, le=20)


class QuizRequest(BaseModel):
    urls: List[str] = Field(min_length=1)
    n_questions: int = Field(default=8, ge=1, le=20)
