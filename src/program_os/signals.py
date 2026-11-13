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


def _text(item: Evidence) -> str:
    return json.dumps(item.payload, sort_keys=True)


def _extract_dates(item: Evidence) -> set[str]:
    text = _text(item)
    dates = set(_ISO_DATE.findall(text))
    for month, day in _MONTH_DATE.findall(text):
        year = item.source_updated_at.year
        month_number = _MONTHS[month[:3].lower()]
        dates.add(f"{year:04d}-{month_number:02d}-{int(day):02d}")
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
    partner_dates: set[str] = set()
    for item in partner:
        partner_dates.update(_extract_dates(item))
    if len(partner_dates) >= 2:
        signals.append(Signal(
            "cross_source_date_conflict",
            "PLAT",
            "high",
            "Partner integration dates conflict across current sources: " + ", ".join(sorted(partner_dates)) + ".",
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

    return signals
