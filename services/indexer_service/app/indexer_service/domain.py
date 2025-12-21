from pydantic import BaseModel, Field
from typing import List, Optional


class CsvArticle(BaseModel):
    title: str
    author: str
    platform: str
    url: str
    content: str
    pub_date: str
    subtopic: str = ""


class ChunkRecord(BaseModel):
    point_id: str
    vector: List[float]
    payload: dict
