"""Loader for plain text and Markdown documents."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from rag.ingestion.base_loader import ArtifactLoader
from rag.models import ArtifactRecord


class TextLoader(ArtifactLoader):
    """Loads UTF-8 text from .txt and .md files."""

    def __init__(self, path: Path) -> None:
        suffix = path.suffix.lower()
        doc_type = "markdown" if suffix in {".md", ".markdown"} else "text"
        super().__init__(path, doc_type=doc_type)

    def _load(self) -> Iterable[ArtifactRecord]:
        try:
            text = self.path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            text = self.path.read_text(encoding="utf-8", errors="ignore")

        text = text.lstrip("\ufeff")

        yield ArtifactRecord(text=text, metadata={"section": "full_text"})
