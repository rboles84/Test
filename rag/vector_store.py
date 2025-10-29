"""Simple persistent vector store backed by SQLite."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List, Optional

import numpy as np

from rag.models import DocumentChunk


@dataclass
class VectorStoreConfig:
    path: Path
    table_name: str = "chunks"


class SQLiteVectorStore:
    """Lightweight vector store suitable for local experimentation."""

    def __init__(self, config: VectorStoreConfig) -> None:
        self.config = config
        self._connection = sqlite3.connect(self.config.path)
        self._ensure_schema()

    def _ensure_schema(self) -> None:
        cursor = self._connection.cursor()
        cursor.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {self.config.table_name} (
                id TEXT PRIMARY KEY,
                embedding BLOB NOT NULL,
                dimension INTEGER NOT NULL,
                text TEXT NOT NULL,
                metadata TEXT NOT NULL
            )
            """
        )
        cursor.execute(
            f"CREATE INDEX IF NOT EXISTS idx_{self.config.table_name}_doc_type ON {self.config.table_name}((json_extract(metadata, '$.doc_type')) )"
        )
        self._connection.commit()

    def upsert(self, chunks: Iterable[DocumentChunk]) -> None:
        cursor = self._connection.cursor()
        for chunk in chunks:
            if chunk.embedding is None:
                raise ValueError("Chunk is missing embedding")
            embedding_array = np.asarray(chunk.embedding, dtype=float)
            cursor.execute(
                f"""
                INSERT INTO {self.config.table_name} (id, embedding, dimension, text, metadata)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    embedding=excluded.embedding,
                    dimension=excluded.dimension,
                    text=excluded.text,
                    metadata=excluded.metadata
                """,
                (
                    chunk.id,
                    embedding_array.tobytes(),
                    embedding_array.shape[-1],
                    chunk.text,
                    json.dumps(chunk.metadata),
                ),
            )
        self._connection.commit()

    def similarity_search(
        self,
        query_embedding: np.ndarray,
        top_k: int = 5,
        filters: Optional[dict] = None,
    ) -> List[DocumentChunk]:
        cursor = self._connection.cursor()
        filter_clause = ""
        params: list = []
        if filters:
            clauses = []
            for key, value in filters.items():
                clauses.append(f"json_extract(metadata, '$.{key}') = ?")
                params.append(value)
            filter_clause = "WHERE " + " AND ".join(clauses)
        cursor.execute(
            f"SELECT id, embedding, dimension, text, metadata FROM {self.config.table_name} {filter_clause}",
            params,
        )
        rows = cursor.fetchall()
        scored: List[tuple[float, DocumentChunk]] = []
        if not rows:
            return []
        for chunk_id, embedding_blob, dimension, text, metadata_json in rows:
            embedding = np.frombuffer(embedding_blob, dtype=float)
            if embedding.shape[0] != dimension:
                continue
            metadata = json.loads(metadata_json)
            score = float(np.dot(query_embedding, embedding) / (
                np.linalg.norm(query_embedding) * np.linalg.norm(embedding) + 1e-10
            ))
            scored.append(
                (
                    score,
                    DocumentChunk(id=chunk_id, text=text, metadata=metadata, embedding=embedding),
                )
            )
        scored.sort(key=lambda item: item[0], reverse=True)
        return [chunk for _, chunk in scored[:top_k]]

    def delete(self, chunk_ids: Iterable[str]) -> None:
        cursor = self._connection.cursor()
        cursor.executemany(
            f"DELETE FROM {self.config.table_name} WHERE id = ?",
            ((chunk_id,) for chunk_id in chunk_ids),
        )
        self._connection.commit()

    def close(self) -> None:
        self._connection.close()
