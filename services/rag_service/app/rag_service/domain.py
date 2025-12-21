from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class RetrievedChunk(BaseModel):
    score: float
    payload: Dict[str, Any]


class AggregatedArticle(BaseModel):
    best_score: float
    payload: Dict[str, Any]
    texts: List[str]
