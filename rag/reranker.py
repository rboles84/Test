"""Optional re-ranking utilities."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List

from rag.models import DocumentChunk


@dataclass
class RerankerConfig:
    enabled: bool = False
    top_k: int | None = None


class IdentityReranker:
    """Default no-op reranker that returns incoming chunks."""

    def rerank(self, chunks: Iterable[DocumentChunk]) -> List[DocumentChunk]:
        return list(chunks)
