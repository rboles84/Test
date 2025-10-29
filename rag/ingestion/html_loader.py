"""Loader for HTML content."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from bs4 import BeautifulSoup

from rag.ingestion.base_loader import ArtifactLoader
from rag.models import ArtifactRecord


class HtmlLoader(ArtifactLoader):
    """Extracts cleaned text from HTML pages."""

    def __init__(self, path: Path) -> None:
        super().__init__(path, doc_type="html")

    def _load(self) -> Iterable[ArtifactRecord]:
        html = self.path.read_text(encoding="utf-8")
        soup = BeautifulSoup(html, "html.parser")
        for script in soup(["script", "style"]):
            script.decompose()
        text = "\n".join(line.strip() for line in soup.get_text().splitlines())
        yield ArtifactRecord(text=text, metadata={"section": "body"})
