"""Loader for Jira export files (JSON)."""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Iterable

from rag.ingestion.base_loader import ArtifactLoader
from rag.models import ArtifactRecord


logger = logging.getLogger(__name__)


class JiraLoader(ArtifactLoader):
    """Parses Jira issue exports (JSON array) into artifact records."""

    def __init__(self, path: Path) -> None:
        super().__init__(path, doc_type="jira")

    def _load(self) -> Iterable[ArtifactRecord]:
        data = json.loads(self.path.read_text(encoding="utf-8"))
        issues_data = data.get("issues") if isinstance(data, dict) else data
        if not isinstance(issues_data, list):
            if issues_data:
                logger.warning(
                    "Expected 'issues' to be a list in %s; found %s. No records will be loaded.",
                    self.path,
                    type(issues_data).__name__,
                )
            issues = []
        else:
            issues = issues_data

        if not issues:
            logger.info("No Jira issues found in %s.", self.path)

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
