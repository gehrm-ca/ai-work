"""Severity-weighted evaluation helpers."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

FAILURE_WEIGHTS = {
    "missed_critical_risk": 5,
    "unsupported_high_confidence_assertion": 5,
    "incorrect_hard_gate": 4,
    "missed_material_contradiction": 4,
    "incorrect_evidence_citation": 4,
    "harmful_portfolio_intervention": 4,
    "failed_insufficient_evidence": 3,
    "incorrect_forecast_direction": 3,
    "incorrect_prioritization": 2,
    "extra_low_severity_alert": 1,
}

CATASTROPHIC_FAILURES = {
    "fabricated_material_evidence",
    "high_confidence_green_with_mandatory_blocker",
    "missed_explicit_launch_critical_risk",
    "consequential_action_without_evidence_or_tradeoffs",
}


@dataclass(frozen=True)
class EvalFailure:
    kind: str
    case_id: str
    detail: str = ""


@dataclass(frozen=True)
class EvalSummary:
    weighted_penalty: int
    catastrophic: bool
    catastrophic_failures: tuple[EvalFailure, ...]


def summarize_failures(failures: Iterable[EvalFailure]) -> EvalSummary:
    failures = tuple(failures)
    weighted = sum(FAILURE_WEIGHTS.get(f.kind, 0) for f in failures)
    catastrophic_items = tuple(f for f in failures if f.kind in CATASTROPHIC_FAILURES)
    return EvalSummary(
        weighted_penalty=weighted,
        catastrophic=bool(catastrophic_items),
        catastrophic_failures=catastrophic_items,
    )
