from __future__ import annotations

import json
from pathlib import Path

from rag.ingestion.jira_loader import JiraLoader


def test_load_returns_empty_list_when_issues_missing(tmp_path: Path) -> None:
    payload = {"project": {"name": "Example"}}
    path = tmp_path / "jira.json"
    path.write_text(json.dumps(payload), encoding="utf-8")

    loader = JiraLoader(path)

    assert loader.load() == []
