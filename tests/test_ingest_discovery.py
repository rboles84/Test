import sys
import types
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

# Stub heavy optional dependencies so the module under test can be imported without
# requiring external packages such as numpy, scikit-learn, or BeautifulSoup.
stub_modules = {
    "rag.embedder": {"EmbeddingClient": object, "EmbeddingConfig": object},
    "rag.ingestion.html_loader": {"HtmlLoader": object},
    "rag.ingestion.jira_loader": {"JiraLoader": object},
    "rag.ingestion.pdf_loader": {"PdfLoader": object},
    "rag.ingestion.spreadsheet_loader": {"SpreadsheetLoader": object},
    "rag.vector_store": {"SQLiteVectorStore": object, "VectorStoreConfig": object},
}

for name, attributes in stub_modules.items():
    module = types.ModuleType(name)
    module.__dict__.update(attributes)
    sys.modules.setdefault(name, module)

from rag.ingest import discover_artifacts


def test_discover_artifacts_handles_uppercase_suffixes(tmp_path: Path) -> None:
    docs_dir = tmp_path / "docs"
    docs_dir.mkdir()

    supported_files = [
        docs_dir / "ticket.PDF",
        docs_dir / "runbook.HTML",
        docs_dir / "report.CsV",
    ]
    for file_path in supported_files:
        file_path.write_text("stub")

    # Add an unsupported file to ensure it is ignored.
    (docs_dir / "notes.txt").write_text("ignore me")

    discovered = discover_artifacts([tmp_path])

    assert set(supported_files).issubset(set(discovered))
