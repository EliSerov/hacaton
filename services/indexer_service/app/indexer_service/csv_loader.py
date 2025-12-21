from pathlib import Path
from typing import Iterable, List
import pandas as pd
from indexer_service.domain import CsvArticle


class CsvDirectoryLoader:
    def __init__(self, input_dir: str) -> None:
        self._input_dir = Path(input_dir)

    def list_csv_files(self) -> List[Path]:
        if self._input_dir.is_file() and self._input_dir.suffix.lower() == ".csv":
            return [self._input_dir]
        return sorted(self._input_dir.glob("*.csv"))

    def iter_articles(self) -> Iterable[CsvArticle]:
        for csv_path in self.list_csv_files():
            df = pd.read_csv(csv_path)
            # Expecting columns:
            # id, title, author, platform, url, content, pub_date, subtopic
            for _, row in df.iterrows():
                yield CsvArticle(
                    title=str(row.get("title", "") or ""),
                    author=str(row.get("author", "") or ""),
                    platform=str(row.get("platform", "") or ""),
                    url=str(row.get("url", "") or ""),
                    content=str(row.get("content", "") or ""),
                    pub_date=str(row.get("pub_date", "") or ""),
                    subtopic=str(row.get("subtopic", "") or ""),
                )
