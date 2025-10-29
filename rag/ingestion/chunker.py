"""Chunking utilities for artifact records."""
from __future__ import annotations

import hashlib
from typing import Iterable, List

from rag.models import ArtifactRecord, DocumentChunk, merge_metadata


def chunk_text(text: str, chunk_size: int, overlap: int) -> Iterable[str]:
    words = text.split()
    if not words:
        return []
    step = max(chunk_size - overlap, 1)
    for start in range(0, len(words), step):
        chunk_words = words[start : start + chunk_size]
        if not chunk_words:
            continue
        yield " ".join(chunk_words)


def chunk_records(
    records: Iterable[ArtifactRecord],
    chunk_size: int = 200,
    overlap: int = 40,
    prefix: str | None = None,
) -> List[DocumentChunk]:
    """Chunk artifact records into DocumentChunk instances."""

    chunks: List[DocumentChunk] = []
    for record in records:
        for index, text_chunk in enumerate(chunk_text(record.text, chunk_size, overlap)):
            chunk_id_source = f"{prefix or 'chunk'}-{record.metadata.get('source', '')}-{index}-{text_chunk[:32]}"
            chunk_id = hashlib.sha1(chunk_id_source.encode("utf-8")).hexdigest()
            chunks.append(
                DocumentChunk(
                    id=chunk_id,
                    text=text_chunk,
                    metadata=merge_metadata(record.metadata, {"chunk_index": str(index)}),
                )
            )
    return chunks
