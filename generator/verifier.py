"""Verification helpers for generated test cases."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, Protocol


class Verifier(Protocol):
    def verify(self, llm_output: str) -> "VerificationResult":
        ...


@dataclass
class VerificationResult:
    passed: bool
    details: Dict[str, str]

    def to_dict(self) -> Dict[str, str]:
        return {"passed": str(self.passed), **self.details}


class JsonSchemaVerifier:
    """Performs simple JSON decoding to ensure structural validity."""

    def verify(self, llm_output: str) -> VerificationResult:
        try:
            json.loads(llm_output)
            return VerificationResult(passed=True, details={"reason": "Valid JSON"})
        except json.JSONDecodeError as exc:
            return VerificationResult(passed=False, details={"error": str(exc)})
