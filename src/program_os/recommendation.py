"""Portfolio-level intervention recommendation for the Atlas vertical slice."""
from __future__ import annotations

from typing import Iterable

from .models import ConfidenceBand, Evidence, Recommendation
from .signals import Signal


def recommend_resource_tradeoff(
    signals: Iterable[Signal],
    evidence: Iterable[Evidence],
    *,
    system_version: str = "0.2.0",
) -> Recommendation | None:
    signals = list(signals)
    by_id = {item.evidence_id: item for item in evidence}

    resource = next((s for s in signals if s.kind == "resource_overallocation"), None)
    dependency = next((s for s in signals if s.kind == "cross_source_date_conflict"), None)
    if not resource or not dependency:
        return None

    preferred_ids = [
        evidence_id for evidence_id in (
            "RES-1112",
            "ATLAS-101",
            "ATLAS-109",
            "DEP-MAP-1112",
            "MTG-1111-PORTFOLIO",
        )
        if evidence_id in by_id
    ]
    return Recommendation(
        recommendation_id="rec-atlas-resource-01",
        project_id="atlas",
        action=(
            "Temporarily prioritize Maya's Platform integration recovery work and "
            "explicitly sequence or reassign her AI citation-evaluator support."
        ),
        expected_benefit=(
            "Protect the critical partner-integration dependency that feeds the release "
            "candidate and launch-readiness work."
        ),
        downstream_consequences=[
            "AI citation-evaluator support may slip unless an alternate owner is assigned.",
            "Any reallocation must be reviewed against the AI launch-threshold milestone.",
        ],
        confidence=ConfidenceBand.MODERATE,
        evidence_ids=preferred_ids,
        approval_required=True,
        system_version=system_version,
    )
