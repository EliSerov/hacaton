from typing import Any, Dict, List
from common.contracts.models import ArticleItem, RagResponse


class ContractMapper:
    def to_contract(self, summary: str, articles: List[Dict[str, Any]]) -> Dict[str, Any]:
        items = []
        for a in articles:
            items.append(ArticleItem(
                title=a["title"],
                url=a["url"],
                author=a.get("author", "") or "",
                date=a.get("date", "") or "",
                topic=a.get("topic", "") or "",
            ))
        resp = RagResponse(summary=summary, articles=items)
        return resp.model_dump()
