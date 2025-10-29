"""Embedding utilities for the RAG pipeline."""
from __future__ import annotations

import importlib
from dataclasses import dataclass
from typing import Iterable, List

import numpy as np
from sklearn.feature_extraction.text import HashingVectorizer


@dataclass
class EmbeddingConfig:
    model_name: str = "sentence-transformers/all-MiniLM-L6-v2"
    batch_size: int = 32


class EmbeddingClient:
    """Lightweight wrapper that can use a sentence-transformer or a hashing fallback."""

    def __init__(self, config: EmbeddingConfig | None = None) -> None:
        self.config = config or EmbeddingConfig()
        self._vectorizer = HashingVectorizer(n_features=1024, alternate_sign=False)
        self._sentence_model = self._load_sentence_transformer()

    def _load_sentence_transformer(self):
        spec = importlib.util.find_spec("sentence_transformers")
        if spec is None:
            return None
        module = importlib.import_module("sentence_transformers")
        return module.SentenceTransformer(self.config.model_name)

    def embed(self, texts: Iterable[str]) -> List[np.ndarray]:
        texts_list = list(texts)
        if self._sentence_model is not None:
            embeddings = self._sentence_model.encode(texts_list, batch_size=self.config.batch_size)
            return [np.asarray(embedding, dtype=float) for embedding in embeddings]
        hashed = self._vectorizer.transform(texts_list)
        return [row.toarray().astype(float).ravel() for row in hashed]

    def embed_query(self, text: str) -> np.ndarray:
        return self.embed([text])[0]
