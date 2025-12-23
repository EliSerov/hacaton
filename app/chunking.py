from __future__ import annotations
from dataclasses import dataclass

@dataclass
class Chunk:
    text: str
    index: int

def chunk_text(text: str, chunk_size: int, overlap: int) -> list[Chunk]:
    if not text:
        return []
    t = str(text).strip()
    if len(t) <= chunk_size:
        return [Chunk(t, 0)]
    out: list[Chunk] = []
    start = 0
    idx = 0
    while start < len(t):
        end = min(len(t), start + chunk_size)
        part = t[start:end].strip()
        if part:
            out.append(Chunk(part, idx))
            idx += 1
        if end >= len(t):
            break
        start = max(0, end - overlap)
    return out
