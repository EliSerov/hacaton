import re
from datetime import datetime
from typing import List, Tuple


def norm_text(s: str) -> str:
    s = (s or "").strip()
    s = re.sub(r"\s+", " ", s)
    return s


def norm_key(s: str) -> str:
    return norm_text(s).lower()


def parse_topics(subtopic: str) -> Tuple[List[str], List[str], str]:
    raw = norm_text(subtopic)
    parts = [p.strip() for p in raw.split(",") if p.strip()]
    if not parts:
        parts = ["unknown"]
    return parts, [p.lower() for p in parts], raw


def to_pub_day(pub_date: str) -> str:
    # robust ISO parsing
    dt = datetime.fromisoformat(pub_date.replace("Z", "+00:00"))
    return dt.date().isoformat()
