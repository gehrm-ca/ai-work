"""Structured design-partner pilot records.

Pilot files may contain sensitive program context and belong under ignored local
storage (for example var/pilots/). Public repository artifacts should contain only
reviewed aggregate or syntheticized results.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from .models import ConfidenceBand, Rag


class PilotDisposition(str, Enum):
    ACCEPT = "Accept"
    MODIFY = "Modify"
    REJECT = "Reject"
    MONITOR = "Monitor"


class PilotFindingType(str, Enum):
    RISK = "risk"
    CONTRADICTION = "contradiction"
    FORECAST = "forecast"
    RECOMMENDATION = "recommendation"
    MISSING_INFORMATION = "missing_information"


class PilotBaseline(BaseModel):
    model_config = ConfigDict(frozen=True)

    recorded_at: datetime
    official_rag: Rag
    forecast_expectation: str
    known_risks: tuple[str, ...] = ()
    known_dependencies: tuple[str, ...] = ()
    next_milestone: str | None = None
    intervention_priorities: tuple[str, ...] = ()
    unresolved_decisions: tuple[str, ...] = ()
    plan_confidence: ConfidenceBand


class PilotEvidenceSnapshot(BaseModel):
    model_config = ConfigDict(frozen=True)

    snapshot_id: str
    captured_at: datetime
    source_types: tuple[str, ...]
    evidence_count: int = Field(ge=1)
    private_location: str | None = None
    public_data: bool = False


class PilotFindingReview(BaseModel):
    model_config = ConfigDict(frozen=True)

    finding_id: str
    finding_type: PilotFindingType
    material: bool = True
    disposition: PilotDisposition
    rationale: str
    action_taken: str | None = None
    expected_consequence: str | None = None
    eventual_outcome: str | None = None
    evidence_ids: tuple[str, ...] = ()


class PilotCommercialSignal(BaseModel):
    model_config = ConfigDict(frozen=True)

    would_run_again_next_week: bool
    would_use_in_real_operating_review: bool
    buyer_role: str | None = None
    willingness_to_continue_paid_pilot: bool | None = None
    pricing_reaction: str | None = None


class PilotRecord(BaseModel):
    pilot_id: str
    program_alias: str
    started_at: datetime
    baseline: PilotBaseline | None = None
    evidence_snapshot: PilotEvidenceSnapshot | None = None
    findings: list[PilotFindingReview] = Field(default_factory=list)
    commercial_signal: PilotCommercialSignal | None = None
    final_readout: str | None = None

    @property
    def ready_for_analysis(self) -> bool:
        return self.baseline is not None and self.evidence_snapshot is not None

    def aggregate_summary(self) -> dict[str, Any]:
        dispositions = Counter(item.disposition.value for item in self.findings)
        material = [item for item in self.findings if item.material]
        material_accept_or_modify = sum(
            1
            for item in material
            if item.disposition in {
                PilotDisposition.ACCEPT,
                PilotDisposition.MODIFY,
            }
        )
        return {
            "pilot_id": self.pilot_id,
            "ready_for_analysis": self.ready_for_analysis,
            "finding_count": len(self.findings),
            "material_finding_count": len(material),
            "dispositions": dict(sorted(dispositions.items())),
            "material_accept_or_modify_count": material_accept_or_modify,
            "commercial_signal_recorded": self.commercial_signal is not None,
            "would_run_again_next_week": (
                self.commercial_signal.would_run_again_next_week
                if self.commercial_signal
                else None
            ),
            "would_use_in_real_operating_review": (
                self.commercial_signal.would_use_in_real_operating_review
                if self.commercial_signal
                else None
            ),
            "willingness_to_continue_paid_pilot": (
                self.commercial_signal.willingness_to_continue_paid_pilot
                if self.commercial_signal
                else None
            ),
        }


def new_pilot_record(pilot_id: str, program_alias: str) -> PilotRecord:
    return PilotRecord(
        pilot_id=pilot_id,
        program_alias=program_alias,
        started_at=datetime.now(timezone.utc),
    )
