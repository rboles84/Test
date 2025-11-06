# Test Case Generator (WIP)

This repository bootstraps a Retrieval-Augmented Generation (RAG) workflow that uses a Master Orchestration Prompt (MOP) to produce consistent, ISTQB-aligned test cases from artifacts such as Jira tickets, acceptance criteria, and domain standards.

## Repository Layout

```
config/
  rag.yml               # Default configuration for embeddings, vector store, and retrieval

evaluation/
  static_checks.py      # Automated validation helpers for generated test suites

generator/
  pipeline.py           # Orchestrates retrieval, prompting, LLM calls, and verification
  verifier.py           # Minimal verification framework (JSON schema check)

prompts/
  master_orchestration_prompt.md  # Test Case Copilot persona and decision flow

rag/
  ingest.py             # CLI to ingest artifacts into the vector store
  embedder.py           # Embedding client with sentence-transformer or hashing fallback
  models.py             # Shared dataclasses for records and chunks
  retriever.py          # Semantic retriever using the vector store
  reranker.py           # Optional reranker placeholder
  vector_store.py       # SQLite-backed persistent vector store
  ingestion/
    base_loader.py      # Base loader contract
    pdf_loader.py       # PDF ingestion using `pypdf`
    html_loader.py      # HTML ingestion with BeautifulSoup
    jira_loader.py      # Jira JSON export ingestion
    spreadsheet_loader.py  # CSV/XLSX ingestion via `csv` and `openpyxl`
    chunker.py          # Chunking utilities

sample1_MOP_TestCaseCreator/
  ...                   # Example sub-prompt referenced by the MOP
```

## Getting Started

1. **Install dependencies** (Python 3.10+ recommended):

   ```bash
   pip install -r requirements.txt  # create if you maintain a requirements file
   pip install pypdf beautifulsoup4 openpyxl scikit-learn sentence-transformers PyYAML
   ```

2. **Configure the vector store** by updating `config/rag.yml`. The default setup stores embeddings in `data/vector_store.sqlite`. Create the directory if it does not exist:

   ```bash
   mkdir -p data
   ```

3. **Ingest artifacts** (PDFs, HTML pages, Jira JSON exports, CSV/XLSX spreadsheets) using the CLI:

   ```bash
   python -m rag.ingest ./artifacts --config config/rag.yml --chunk-size 200 --overlap 40
   ```

   The command walks the provided directory, converts artifacts to text with metadata, chunks the text, computes embeddings, and upserts them into the SQLite vector store. Supported artifacts are discovered regardless of file extension casing (for example, `.PDF`, `.HTML`, and `.CsV`).

4. **Wire up the generator** by instantiating `TestCaseGenerator` with an LLM callable:

   ```python
   from pathlib import Path
   from generator.pipeline import GeneratorConfig, PromptConfig, TestCaseGenerator
   from rag.retriever import RetrieverConfig
   from rag.vector_store import VectorStoreConfig

   def call_llm(prompt: str) -> str:
       # Replace with an actual LLM invocation (OpenAI, Azure, Anthropic, etc.)
       raise NotImplementedError

   generator = TestCaseGenerator(
       config=GeneratorConfig(
           retriever=RetrieverConfig(
               vector_store=VectorStoreConfig(path=Path("data/vector_store.sqlite")),
           ),
           prompt=PromptConfig(master_prompt_path=Path("prompts/master_orchestration_prompt.md")),
       ),
       llm_callable=call_llm,
   )

   response = generator.generate(
       {
           "summary": "As a policy admin, I can renew a policy",
           "acceptance_criteria": "Given ...",
           "artifacts": "",
       }
   )
   ```

   The generator retrieves relevant context, builds the MOP prompt, and returns both the prompt sent to the LLM and the raw response. Attach a verifier (e.g., `JsonSchemaVerifier`) to enforce structured outputs.

5. **Evaluate outputs** using helpers in `evaluation/static_checks.py` to ensure coverage and JSON validity. Extend this module with additional domain-specific checks as the system evolves.

## Next Steps

- Implement advanced reranking (cross-encoder or LLM-based).
- Add dedicated sub-prompts for functional, integration, and regression modules.
- Integrate automated regression evaluation against curated gold standards and feed reviewer comments back into prompt versions.
