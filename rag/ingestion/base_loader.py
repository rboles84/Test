"""Base classes and utilities for artifact loaders."""
from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Iterable, List, Sequence

from rag.models import ArtifactRecord, ensure_metadata_path


class ArtifactLoader(ABC):
    """Abstract loader that converts artifacts into plain text records."""

    def __init__(self, path: Path, doc_type: str | None = None) -> None:
        self.path = Path(path)
        self.doc_type = doc_type or self.path.suffix.lstrip(".")

    def load(self) -> List[ArtifactRecord]:
        records = list(self._load())
        metadata = {"doc_type": self.doc_type}
        with_path = [
            record.with_metadata(**ensure_metadata_path(record.metadata, self.path), **metadata)
            for record in records
        ]
        return with_path

    @abstractmethod
    def _load(self) -> Iterable[ArtifactRecord]:
        """Yield artifact records extracted from the underlying file."""


def batched(iterable: Sequence[str], batch_size: int) -> Iterable[Sequence[str]]:
    for idx in range(0, len(iterable), batch_size):
        yield iterable[idx : idx + batch_size]
