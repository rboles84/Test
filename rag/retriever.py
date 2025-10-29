"""Semantic retriever built on the vector store."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from rag.embedder import EmbeddingClient, EmbeddingConfig
from rag.models import DocumentChunk
from rag.vector_store import SQLiteVectorStore, VectorStoreConfig


@dataclass
class RetrieverConfig:
    vector_store: VectorStoreConfig
    embedding: EmbeddingConfig | None = None
    top_k: int = 5


class SemanticRetriever:
    def __init__(self, config: RetrieverConfig) -> None:
        self.config = config
        self.embedder = EmbeddingClient(config.embedding)
        self.vector_store = SQLiteVectorStore(config.vector_store)

    def retrieve(
        self,
        query: str,
        top_k: Optional[int] = None,
        filters: Optional[Dict[str, str]] = None,
    ) -> List[DocumentChunk]:
        query_embedding = self.embedder.embed_query(query)
        return self.vector_store.similarity_search(query_embedding, top_k or self.config.top_k, filters)

    def close(self) -> None:
        self.vector_store.close()
