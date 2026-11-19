"""Deterministic signal detection for the Atlas V2 vertical slice."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from datetime import datetime
from typing import Iterable

from .models import Evidence

_ISO_DATE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
_MONTH_DATE = re.compile(
    r"\b(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(\d{1,2})\b",
    re.IGNORECASE,
)
_MONTHS = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}


@dataclass(frozen=True)
class Signal:
    kind: str
    project_id: str
    severity: str
    summary: str
    evidence_ids: tuple[str, ...]
    reasoning_factors: tuple[str, ...] = ()
    what_would_change: tuple[str, ...] = ()


_SIGNAL_GUIDANCE: dict[str, dict[str, tuple[str, ...]]] = {
    "resource_overallocation": {
        "reasoning_factors": (
            "A shared critical resource is allocated beyond available capacity across concurrent launch work.",
        ),
        "what_would_change": (
            "A current resource plan shows the shared resource at or below full capacity, or an alternate owner is assigned without moving a critical milestone.",
        ),
    },
    "worsening_defect_trend": {
        "reasoning_factors": (
            "Multiple test cycles show high-severity defects rising while overall pass rate declines.",
        ),
        "what_would_change": (
            "Fresh test evidence shows the high-defect trend reversing and readiness metrics recovering to the agreed launch threshold.",
        ),
    },
    "unapproved_scope_change": {
        "reasoning_factors": (
            "Delivery work tagged as new scope is active while the corresponding formal scope decision is still pending.",
        ),
        "what_would_change": (
            "The scope change is formally approved or rejected and implementation plus downstream commitments are reconciled to that decision.",
        ),
    },
    "cross_source_date_conflict": {
        "reasoning_factors": (
            "Current sources state incompatible completion dates for the same critical-path partner integration.",
        ),
        "what_would_change": (
            "Fresh authoritative planning and execution evidence converges on one partner-integration completion date and the critical-path baseline is updated.",
        ),
    },
    "launch_threshold_gap": {
        "reasoning_factors": (
            "The observed readiness metric is below the documented launch threshold.",
        ),
        "what_would_change": (
            "Current test evidence meets or exceeds the documented threshold, or an authorized decision formally changes the threshold.",
        ),
    },
    "approval_timing_risk": {
        "reasoning_factors": (
            "Mandatory compliance sign-off is scheduled near a period when the named approver is unavailable.",
        ),
        "what_would_change": (
            "The required sign-off is completed early or a confirmed backup approver has authority and availability before the critical date.",
        ),
    },
    "official_status_lag": {
        "reasoning_factors": (
            "The latest official GREEN predates fresher operational evidence that contains high-severity delivery signals.",
        ),
        "what_would_change": (
            "A new official status reconciles the fresher evidence, or the underlying operational signals are corrected or demonstrably resolved.",
        ),
    },
}


def _with_guidance(signal: Signal) -> Signal:
    guidance = _SIGNAL_GUIDANCE.get(signal.kind, {})
    return Signal(
        kind=signal.kind,
        project_id=signal.project_id,
        severity=signal.severity,
        summary=signal.summary,
        evidence_ids=signal.evidence_ids,
        reasoning_factors=guidance.get("reasoning_factors", ()),
        what_would_change=guidance.get("what_would_change", ()),
    )


def _text(item: Evidence) -> str:
    return json.dumps(item.payload, sort_keys=True)


def _dates_in(text: str, default_year: int) -> set[str]:
    dates = set(_ISO_DATE.findall(text))
    for month, day in _MONTH_DATE.findall(text):
        month_number = _MONTHS[month[:3].lower()]
        dates.add(f"{default_year:04d}-{month_number:02d}-{int(day):02d}")
    return dates


def _names_partner_integration(text: str) -> bool:
    lowered = text.lower()
    return "partner" in lowered and "integration" in lowered


def _partner_integration_dates(item: Evidence) -> set[str]:
    """Dates this record states for the partner integration itself.

    A record can mention the partner integration and still hold many dates that
    belong to other work: a milestone plan, a dependency map, a launch plan.
    Only three places count, so unrelated dates never read as a conflict:

    1. the record's own date fields, when its title names the integration;
    2. milestones whose name names the integration;
    3. free-text statements that name the integration.

    Dependency "required by" dates are downstream need-by dates, not dates for
    the integration, so they are left out.
    """
    payload = item.payload
    year = item.source_updated_at.year
    dates: set[str] = set()

    if _names_partner_integration(str(payload.get("title", ""))):
        for key in ("due_date", "target_date", "forecast_date", "date"):
            value = payload.get(key)
            if isinstance(value, str):
                dates |= _dates_in(value, year)

    for milestone in payload.get("milestones", []):
        if isinstance(milestone, dict):
            name, value = milestone.get("name", ""), milestone.get("date", "")
        elif isinstance(milestone, (list, tuple)) and len(milestone) >= 2:
            name, value = milestone[0], milestone[1]
        else:
            continue
        if _names_partner_integration(str(name)):
            dates |= _dates_in(str(value), year)

    statements = [payload.get(key) for key in ("notes", "summary", "finding")]
    statements += list(payload.get("statements", []))
    for statement in statements:
        if isinstance(statement, str) and _names_partner_integration(statement):
            dates |= _dates_in(statement, year)

    return dates


def detect_signals(evidence: Iterable[Evidence]) -> list[Signal]:
    items = list(evidence)
    signals: list[Signal] = []

    # Shared-resource contention.
    resource_ids: list[str] = []
    names: list[str] = []
    for item in items:
        if item.source_type != "resource_plan":
            continue
        for person in item.payload.get("people", []):
            allocations = person.get("allocations", {})
            if person.get("overallocated") or sum(allocations.values()) > 1.0:
                resource_ids.append(item.evidence_id)
                names.append(person.get("name", "resource"))
    if resource_ids:
        signals.append(Signal(
            "resource_overallocation",
            "atlas",
            "high",
            f"Shared resource overallocation detected for {', '.join(sorted(set(names)))}.",
            tuple(sorted(set(resource_ids))),
        ))

    # Quality trend.
    tests = sorted(
        (item for item in items if item.source_type == "test_system"),
        key=lambda item: item.source_updated_at,
    )
    if len(tests) >= 3:
        high_counts = [int(item.payload.get("open_defects", {}).get("high", 0)) for item in tests]
        pass_rates = [float(item.payload.get("pass_rate", 1.0)) for item in tests]
        if high_counts == sorted(high_counts) and high_counts[-1] > high_counts[0] and pass_rates[-1] < pass_rates[0]:
            signals.append(Signal(
                "worsening_defect_trend",
                tests[-1].project_id,
                "high",
                f"High defects increased {high_counts[0]}→{high_counts[-1]} while pass rate fell {pass_rates[0]:.2f}→{pass_rates[-1]:.2f}.",
                tuple(item.evidence_id for item in tests),
            ))

    # Unapproved scope entering delivery.
    scope_work = [
        item for item in items
        if item.source_type == "jira" and item.payload.get("scope_tag") == "new"
    ]
    pending_scope_decisions = [
        item for item in items
        if item.source_type == "decision_log"
        and item.payload.get("status") == "Pending"
        and "scope" in _text(item).lower() or (
            item.source_type == "decision_log"
            and item.payload.get("status") == "Pending"
            and "export filtering" in _text(item).lower()
        )
    ]
    if scope_work and pending_scope_decisions:
        signals.append(Signal(
            "unapproved_scope_change",
            "atlas",
            "high",
            "Active implementation exists for new scope that is not formally approved.",
            tuple(item.evidence_id for item in (scope_work + pending_scope_decisions)),
        ))

    # Partner integration date conflict.
    partner = [
        item for item in items
        if "partner" in _text(item).lower() and "integration" in _text(item).lower()
    ]
    # Map each stated date to the records that state it, so the finding names
    # which source says what instead of listing every date in those records.
    partner_dates: dict[str, list[str]] = {}
    for item in partner:
        for stated in _partner_integration_dates(item):
            partner_dates.setdefault(stated, []).append(item.evidence_id)
    if len(partner_dates) >= 2:
        stated_dates = ", ".join(
            f"{stated} ({', '.join(sorted(sources))})"
            for stated, sources in sorted(partner_dates.items())
        )
        signals.append(Signal(
            "cross_source_date_conflict",
            "PLAT",
            "high",
            "Partner integration dates conflict across current sources: " + stated_dates + ".",
            tuple(item.evidence_id for item in partner),
        ))

    # Launch threshold gap.
    threshold_items = [item for item in items if item.source_type == "confluence" and "launch_thresholds" in item.payload]
    metric_items = [item for item in items if item.source_type == "jira" and "pass_rate" in item.payload]
    for threshold_item in threshold_items:
        threshold = threshold_item.payload.get("launch_thresholds", {}).get("refusal_pass_rate")
        for metric_item in metric_items:
            rate = metric_item.payload.get("pass_rate")
            if threshold is not None and rate is not None and float(rate) < float(threshold):
                signals.append(Signal(
                    "launch_threshold_gap",
                    metric_item.project_id,
                    "high",
                    f"Observed refusal-test pass rate {float(rate):.2f} is below launch threshold {float(threshold):.2f}.",
                    (metric_item.evidence_id, threshold_item.evidence_id),
                ))

    # Approval timing exposure.
    approval_decisions = [
        item for item in items
        if item.source_type == "decision_log" and "approver sign-off required" in _text(item).lower()
    ]
    approval_notes = [
        item for item in items
        if item.source_type == "meeting_notes" and "approver is out" in _text(item).lower()
    ]
    if approval_decisions and approval_notes:
        signals.append(Signal(
            "approval_timing_risk",
            "SEC",
            "high",
            "Mandatory compliance sign-off has a named-approver availability risk near the evidence-package deadline.",
            tuple(item.evidence_id for item in (approval_decisions + approval_notes)),
        ))

    # Official GREEN may lag fresher high-severity evidence.
    green_statuses = [
        item for item in items
        if item.source_type == "exec_status" and item.payload.get("portfolio_rag") == "GREEN"
    ]
    if green_statuses and any(signal.severity == "high" for signal in signals):
        latest_status = max(green_statuses, key=lambda item: item.source_updated_at)
        fresher = [
            item for item in items
            if item.source_updated_at > latest_status.source_updated_at
            and item.source_type in {"jira", "test_system", "meeting_notes", "resource_plan"}
        ]
        if fresher:
            signals.append(Signal(
                "official_status_lag",
                "atlas",
                "high",
                "Official portfolio GREEN predates fresher operational evidence carrying material risk signals.",
                tuple([latest_status.evidence_id] + [item.evidence_id for item in fresher[:6]]),
            ))

    return [_with_guidance(signal) for signal in signals]
