"""Loader for Jira export files (JSON)."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List

from rag.ingestion.base_loader import ArtifactLoader
from rag.models import ArtifactRecord


class JiraLoader(ArtifactLoader):
    """Parses Jira issue exports (JSON array) into artifact records."""

    def __init__(self, path: Path) -> None:
        super().__init__(path, doc_type="jira")

    def _load(self) -> Iterable[ArtifactRecord]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        issues: List[dict] = data.get("issues") if isinstance(data, dict) else data
        for issue in issues:
            key = issue.get("key")
            fields = issue.get("fields", {})
            summary = fields.get("summary", "")
            description = fields.get("description", "")
            text = f"Summary: {summary}\nDescription: {description}".strip()
            metadata = {
                "jira_key": key or "",
                "status": fields.get("status", {}).get("name", ""),
                "assignee": fields.get("assignee", {}).get("displayName", ""),
                "issue_type": fields.get("issuetype", {}).get("name", ""),
            }
            yield ArtifactRecord(text=text, metadata={k: v for k, v in metadata.items() if v})
