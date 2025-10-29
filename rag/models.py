"""Shared data models for the RAG pipeline."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, Iterable, List, Optional


@dataclass
class ArtifactRecord:
    """Represents a unit of text extracted from an artifact before chunking."""

    text: str
    metadata: Dict[str, str] = field(default_factory=dict)

    def with_metadata(self, **metadata: str) -> "ArtifactRecord":
        updated = self.metadata.copy()
        updated.update({k: str(v) for k, v in metadata.items() if v is not None})
        return ArtifactRecord(text=self.text, metadata=updated)


@dataclass
class DocumentChunk:
    """A chunk of text ready to be embedded and persisted."""

    id: str
    text: str
    metadata: Dict[str, str]
    embedding: Optional[Iterable[float]] = None

    def with_embedding(self, embedding: Iterable[float]) -> "DocumentChunk":
        return DocumentChunk(
            id=self.id,
            text=self.text,
            metadata=self.metadata,
            embedding=list(embedding),
        )


def ensure_metadata_path(metadata: Dict[str, str], source_path: Path) -> Dict[str, str]:
    """Injects normalized path metadata if it is not already defined."""

    if "source" not in metadata:
        metadata = {**metadata, "source": str(source_path)}
    return metadata


def merge_metadata(base: Dict[str, str], extra: Optional[Dict[str, str]]) -> Dict[str, str]:
    merged = dict(base)
    if extra:
        merged.update({k: str(v) for k, v in extra.items()})
    return merged
