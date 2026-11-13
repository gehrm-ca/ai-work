"""Evidence-derived confidence scoring."""
from __future__ import annotations

from dataclasses import dataclass
from math import prod

from .models import ConfidenceBand


@dataclass(frozen=True)
class ConfidenceInputs:
    evidence_quality: float
    source_agreement: float
    freshness: float
    coverage: float
    historical_reliability: float
    mandatory_evidence_missing: bool = False

    def values(self) -> tuple[float, ...]:
        return (
            self.evidence_quality,
            self.source_agreement,
            self.freshness,
            self.coverage,
            self.historical_reliability,
        )


@dataclass(frozen=True)
class ConfidenceResult:
    score: float
    band: ConfidenceBand
    limiting_factors: tuple[str, ...]


def calculate_confidence(inputs: ConfidenceInputs) -> ConfidenceResult:
    values = inputs.values()
    if any(v < 0 or v > 1 for v in values):
        raise ValueError("Confidence factors must be between 0 and 1.")

    score = prod(values) ** (1 / len(values))
    limiting = []
    names = (
        "evidence_quality",
        "source_agreement",
        "freshness",
        "coverage",
        "historical_reliability",
    )
    for name, value in zip(names, values):
        if value < 0.6:
            limiting.append(name)

    if inputs.mandatory_evidence_missing:
        return ConfidenceResult(
            score=min(score, 0.49),
            band=ConfidenceBand.LOW,
            limiting_factors=tuple(limiting + ["mandatory_evidence_missing"]),
        )

    if score >= 0.80:
        band = ConfidenceBand.HIGH
    elif score >= 0.55:
        band = ConfidenceBand.MODERATE
    else:
        band = ConfidenceBand.LOW

    return ConfidenceResult(score=score, band=band, limiting_factors=tuple(limiting))
