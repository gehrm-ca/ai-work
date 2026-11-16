"""Aggregate, content-safe evidence readiness reporting for pilot snapshots.

The report intentionally summarizes structure and coverage without printing source
IDs, project IDs, source URLs, or payload content. It validates whether an
ingestion snapshot is suitable for controlled pilot analysis; it does not claim
that organization-specific semantics are understood by Atlas-specific detectors.
"""
from __future__ import annotations

from collections import Counter
from datetime import datetime
from enum import Enum
from statistics import median

from pydantic import BaseModel, ConfigDict, Field

from .adapters.base import IngestionBatch, SourceRecord


class EvidenceReadinessLevel(str, Enum):
    BLOCKED = "blocked"
    CONNECTOR_READY = "connector_ready"
    PILOT_CANDIDATE = "pilot_candidate"


class EvidenceReadinessReport(BaseModel):
    model_config = ConfigDict(frozen=True)

    connector_id: str
    retrieved_at: datetime
    readiness_level: EvidenceReadinessLevel
    ingestion_complete: bool
    record_count: int = Field(ge=0)
    project_count: int = Field(ge=0)
    source_type_count: int = Field(ge=0)
    source_type_counts: dict[str, int]
    authority_tier_counts: dict[str, int]
    permission_context_coverage_pct: float = Field(ge=0, le=100)
    source_url_coverage_pct: float = Field(ge=0, le=100)
    median_source_age_hours: float | None = Field(default=None, ge=0)
    max_source_age_hours: float | None = Field(default=None, ge=0)
    stale_after_days: int = Field(ge=1)
    stale_record_count: int = Field(ge=0)
    stale_record_pct: float = Field(ge=0, le=100)
    cross_source_evidence_available: bool
    portfolio_evidence_available: bool
    high_authority_evidence_available: bool
    failure_kinds: tuple[str, ...] = ()
    limitations: tuple[str, ...] = ()

    @property
    def suitable_for_pilot_analysis(self) -> bool:
        return self.readiness_level == EvidenceReadinessLevel.PILOT_CANDIDATE


def _has_permission_context(record: SourceRecord) -> bool:
    context = record.permission_context
    return bool(context.principal or context.scopes or context.visibility)


def _percent(numerator: int, denominator: int) -> float:
    if denominator == 0:
        return 0.0
    return round((numerator / denominator) * 100.0, 1)


def assess_evidence_readiness(
    batch: IngestionBatch,
    *,
    stale_after_days: int = 7,
) -> EvidenceReadinessReport:
    """Profile an ingestion batch without exposing source or project identifiers."""
    if stale_after_days < 1:
        raise ValueError("stale_after_days must be at least 1.")

    records = list(batch.records)
    count = len(records)
    source_counts = Counter(record.source_type for record in records)
    authority_counts = Counter(str(record.authority_tier) for record in records)
    project_count = len({record.project_id for record in records})

    permission_count = sum(_has_permission_context(record) for record in records)
    source_url_count = sum(bool(record.source_url) for record in records)

    ages: list[float] = []
    future_timestamp_count = 0
    stale_count = 0
    stale_hours = stale_after_days * 24
    for record in records:
        age_hours = (batch.retrieved_at - record.source_updated_at).total_seconds() / 3600
        if age_hours < 0:
            future_timestamp_count += 1
            age_hours = 0.0
        ages.append(age_hours)
        if age_hours > stale_hours:
            stale_count += 1

    source_type_count = len(source_counts)
    cross_source = source_type_count >= 2
    portfolio = project_count >= 2
    high_authority = any(record.authority_tier <= 2 for record in records)

    limitations: list[str] = []
    if not batch.complete:
        limitations.append(
            "Snapshot is incomplete; denied, malformed, unavailable, or partially "
            "retrieved records must remain explicit during analysis."
        )
    if not records:
        limitations.append("No valid evidence records are available for analysis.")
    if records and not cross_source:
        limitations.append(
            "Only one source type is present; cross-source contradiction detection "
            "cannot be validated from this snapshot."
        )
    if records and not portfolio:
        limitations.append(
            "Only one project/workstream is represented; portfolio tradeoff behavior "
            "cannot be validated from this snapshot."
        )
    if records and permission_count < count:
        limitations.append(
            "Permission context is missing from one or more records; source-access "
            "boundaries are not fully reconstructable."
        )
    if records and not high_authority:
        limitations.append(
            "No authority-tier 1 or 2 evidence is present; consequential conclusions "
            "should remain low-confidence until stronger evidence is available."
        )
    if stale_count:
        limitations.append(
            f"{stale_count} record(s) were older than {stale_after_days} day(s) at "
            "retrieval; freshness must be considered in confidence."
        )
    if future_timestamp_count:
        limitations.append(
            f"{future_timestamp_count} record(s) had source timestamps later than the "
            "retrieval timestamp; clock or source-time semantics require review."
        )

    limitations.append(
        "This profile validates evidence structure and coverage only; it does not "
        "establish organization-specific semantic mapping or compatibility with the "
        "Atlas-specific signal detectors."
    )

    if not batch.complete or not records:
        level = EvidenceReadinessLevel.BLOCKED
    elif cross_source and portfolio and high_authority:
        level = EvidenceReadinessLevel.PILOT_CANDIDATE
    else:
        level = EvidenceReadinessLevel.CONNECTOR_READY

    return EvidenceReadinessReport(
        connector_id=batch.connector_id,
        retrieved_at=batch.retrieved_at,
        readiness_level=level,
        ingestion_complete=batch.complete,
        record_count=count,
        project_count=project_count,
        source_type_count=source_type_count,
        source_type_counts=dict(sorted(source_counts.items())),
        authority_tier_counts=dict(sorted(authority_counts.items())),
        permission_context_coverage_pct=_percent(permission_count, count),
        source_url_coverage_pct=_percent(source_url_count, count),
        median_source_age_hours=round(median(ages), 1) if ages else None,
        max_source_age_hours=round(max(ages), 1) if ages else None,
        stale_after_days=stale_after_days,
        stale_record_count=stale_count,
        stale_record_pct=_percent(stale_count, count),
        cross_source_evidence_available=cross_source,
        portfolio_evidence_available=portfolio,
        high_authority_evidence_available=high_authority,
        failure_kinds=tuple(failure.kind.value for failure in batch.failures),
        limitations=tuple(limitations),
    )
