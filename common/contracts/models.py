from pydantic import BaseModel, Field
from typing import Dict, List, Optional


class RagFilters(BaseModel):
    author: Optional[str] = None
    date: Optional[str] = None  # YYYY-MM-DD
    topic: Optional[str] = None


class RagRequest(BaseModel):
    query: str = Field(..., min_length=1)
    filters: RagFilters = Field(default_factory=RagFilters)


class ArticleItem(BaseModel):
    title: str
    url: str
    author: str
    date: str
    topic: str


class RagResponse(BaseModel):
    summary: str
    articles: List[ArticleItem]
