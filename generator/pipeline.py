"""End-to-end orchestration for the test case generator."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Dict, Iterable, List, Optional

from rag.models import DocumentChunk
from rag.retriever import RetrieverConfig, SemanticRetriever
from rag.reranker import IdentityReranker, RerankerConfig

from generator.verifier import Verifier


@dataclass
class PromptConfig:
    master_prompt_path: Path
    max_context_snippets: int = 5


@dataclass
class GeneratorConfig:
    retriever: RetrieverConfig
    prompt: PromptConfig
    reranker: Optional[RerankerConfig] = None


class PromptBuilder:
    """Loads the Master Orchestration Prompt template and fills context."""

    def __init__(self, config: PromptConfig) -> None:
        self.config = config
        self.template = Path(config.master_prompt_path).read_text(encoding="utf-8")

    def build(
        self,
        user_input: Dict[str, str],
        context_chunks: Iterable[DocumentChunk],
    ) -> str:
        context_lines: List[str] = []
        for chunk in list(context_chunks)[: self.config.max_context_snippets]:
            context_lines.append(
                "\n".join(
                    [
                        "<context>",
                        f"source: {chunk.metadata.get('source', 'unknown')}",
                        f"doc_type: {chunk.metadata.get('doc_type', 'unknown')}",
                        chunk.text,
                        "</context>",
                    ]
                )
            )
        context_block = "\n\n".join(context_lines) if context_lines else "<context>No supporting documents retrieved.</context>"
        payload = {
            **user_input,
            "retrieved_context": context_block,
        }
        prompt = self.template
        for key, value in payload.items():
            prompt = prompt.replace(f"{{{{{key}}}}}", value)
        return prompt


class TestCaseGenerator:
    def __init__(
        self,
        config: GeneratorConfig,
        llm_callable: Callable[[str], str],
        verifier: Optional[Verifier] = None,
    ) -> None:
        self.config = config
        self.llm_callable = llm_callable
        self.retriever = SemanticRetriever(config.retriever)
        reranker_config = config.reranker or RerankerConfig(enabled=False)
        self.reranker = IdentityReranker() if not reranker_config.enabled else IdentityReranker()
        self.prompt_builder = PromptBuilder(config.prompt)
        self.verifier = verifier

    def generate(self, user_input: Dict[str, str]) -> Dict[str, str]:
        query = user_input.get("acceptance_criteria") or user_input.get("summary") or ""
        filters = user_input.get('filters') if isinstance(user_input.get('filters'), dict) else None
        retrieved = self.retriever.retrieve(query, filters=filters)
        reranked = self.reranker.rerank(retrieved)
        prompt = self.prompt_builder.build(user_input, reranked)
        llm_output = self.llm_callable(prompt)
        result = {
            "prompt": prompt,
            "raw_output": llm_output,
            "retrieved_chunks": [chunk.metadata for chunk in reranked],
        }
        if self.verifier is not None:
            verification = self.verifier.verify(llm_output)
            result["verification"] = verification.to_dict()
        return result

    def close(self) -> None:
        self.retriever.close()
