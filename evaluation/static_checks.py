"""Static evaluation utilities for generated test cases."""
from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class CoverageResult:
    missing_criteria: List[str]
    extra_cases: List[str]

    @property
    def passed(self) -> bool:
        return not self.missing_criteria and not self.extra_cases


def validate_json_schema(output: str) -> bool:
    try:
        json.loads(output)
        return True
    except json.JSONDecodeError:
        return False


def check_acceptance_criteria_coverage(
    acceptance_criteria: List[str],
    generated_cases: List[Dict[str, str]],
) -> CoverageResult:
    normalized_cases = {case.get("id") for case in generated_cases if case.get("id")}
    missing = [criteria for criteria in acceptance_criteria if criteria not in normalized_cases]
    extras = [case_id for case_id in normalized_cases if case_id not in acceptance_criteria]
    return CoverageResult(missing_criteria=missing, extra_cases=extras)
