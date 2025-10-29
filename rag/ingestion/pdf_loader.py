"""Loader for PDF artifacts."""
from __future__ import annotations

from pathlib import Path
from typing import Iterable

from pypdf import PdfReader

from rag.ingestion.base_loader import ArtifactLoader
from rag.models import ArtifactRecord


class PdfLoader(ArtifactLoader):
    """Extracts text from PDF documents page by page."""

    def __init__(self, path: Path) -> None:
        super().__init__(path, doc_type="pdf")

    def _load(self) -> Iterable[ArtifactRecord]:
        reader = PdfReader(str(self.path))
        for page_number, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            if text.strip():
                yield ArtifactRecord(
                    text=text,
                    metadata={"page": str(page_number)},
                )
