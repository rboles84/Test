"""Command-line entry point for ingesting artifacts into the vector store."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable, List

from rag.embedder import EmbeddingClient, EmbeddingConfig
from rag.ingestion.chunker import chunk_records
from rag.ingestion.html_loader import HtmlLoader
from rag.ingestion.jira_loader import JiraLoader
from rag.ingestion.pdf_loader import PdfLoader
from rag.ingestion.spreadsheet_loader import SpreadsheetLoader
from rag.models import ArtifactRecord, DocumentChunk
from rag.vector_store import SQLiteVectorStore, VectorStoreConfig

LOADER_MAPPING = {
    ".pdf": PdfLoader,
    ".html": HtmlLoader,
    ".htm": HtmlLoader,
    ".json": JiraLoader,
    ".csv": SpreadsheetLoader,
    ".xlsx": SpreadsheetLoader,
    ".xlsm": SpreadsheetLoader,
}


def discover_artifacts(paths: Iterable[Path]) -> List[Path]:
    resolved: List[Path] = []
    for path in paths:
        if path.is_dir():
            for candidate in path.rglob("*"):
                if candidate.is_file() and candidate.suffix.lower() in LOADER_MAPPING:
                    resolved.append(candidate)
        elif path.suffix.lower() in LOADER_MAPPING:
            resolved.append(path)
    return sorted(set(resolved))


def load_records(path: Path) -> List[ArtifactRecord]:
    loader_cls = LOADER_MAPPING.get(path.suffix.lower())
    if loader_cls is None:
        raise ValueError(f"Unsupported artifact type: {path}")
    loader = loader_cls(path)
    return loader.load()


def main() -> None:
    parser = argparse.ArgumentParser(description="Ingest artifacts into the vector store")
    parser.add_argument("paths", nargs="+", type=Path, help="Files or directories to ingest")
    parser.add_argument("--config", type=Path, required=True, help="Path to rag.yml configuration")
    parser.add_argument("--chunk-size", type=int, default=200)
    parser.add_argument("--overlap", type=int, default=40)
    args = parser.parse_args()

    config_data = json.loads(Path(args.config).read_text()) if args.config.suffix == ".json" else None
    if config_data is None:
        import yaml

        config_data = yaml.safe_load(Path(args.config).read_text())

    vector_store_config = VectorStoreConfig(path=Path(config_data["vector_store"]["path"]))
    embedding_config = EmbeddingConfig(**config_data.get("embedding", {}))
    embedder = EmbeddingClient(embedding_config)
    vector_store = SQLiteVectorStore(vector_store_config)

    artifact_paths = discover_artifacts([Path(p) for p in args.paths])
    chunks: List[DocumentChunk] = []
    for artifact_path in artifact_paths:
        records = load_records(artifact_path)
        artifact_chunks = chunk_records(records, args.chunk_size, args.overlap, prefix=artifact_path.stem)
        embeddings = embedder.embed([chunk.text for chunk in artifact_chunks])
        for chunk, embedding in zip(artifact_chunks, embeddings):
            chunks.append(chunk.with_embedding(embedding))
    vector_store.upsert(chunks)
    vector_store.close()
    print(f"Ingested {len(chunks)} chunks into {vector_store_config.path}")


if __name__ == "__main__":
    main()
