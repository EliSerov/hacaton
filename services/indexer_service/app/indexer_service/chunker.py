from typing import List


class SimpleChunker:
    def __init__(self, chunk_size: int, overlap: int) -> None:
        self._chunk_size = chunk_size
        self._overlap = overlap

    def split(self, text: str) -> List[str]:
        text = (text or "").strip()
        if not text:
            return []
        chunks: List[str] = []
        start = 0
        n = len(text)
        while start < n:
            end = min(n, start + self._chunk_size)
            chunks.append(text[start:end])
            if end >= n:
                break
            start = max(0, end - self._overlap)
        return chunks
