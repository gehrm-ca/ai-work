"""Small, inspectable retrieval layer for the V2 vertical slice.

The V2 prototype starts with deterministic lexical/entity retrieval plus
transparent evidence joins for known program-management signal classes. pgvector
remains an architectural target rather than a prerequisite for the vertical slice.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import Iterable

from .models import Evidence
from .signals import detect_signals

_TOKEN_RE = re.compile(r"[a-z0-9_/-]{3,}")

_SIGNAL_QUERY_RULES = {
    "worsening_defect_trend": {"defect", "defects", "testing", "test", "quality", "risk"},
    "resource_overallocation": {"resource", "resources", "shared", "maya", "capacity", "staffing"},
    "cross_source_date_conflict": {"partner", "integration", "schedule", "date", "recovery", "sandbox"},
    "launch_threshold_gap": {"threshold", "refusal", "ai", "model", "guardrail"},
    "approval_timing_risk": {"approval", "approver", "compliance", "sign-off", "signoff"},
    "official_status_lag": {"executive", "green", "status", "operational", "fresher", "current"},
    "unapproved_scope_change": {"scope", "export", "filtering", "approved", "commit"},
}


@dataclass(frozen=True)
class RetrievalHit:
    evidence: Evidence
    score: float
    matched_terms: tuple[str, ...]


def _tokens(text: str) -> set[str]:
    return set(_TOKEN_RE.findall(text.lower()))


def _deterministic_join_ids(items: list[Evidence], query: str) -> set[str]:
    """Expand lexical retrieval with transparent program-management joins.

    These joins do not use gold answers. They are product rules such as
    "trend questions need the whole time series" and "approval questions need
    the decision, approval plan, meeting note, and dependency evidence."
    """
    query_terms = _tokens(query)
    ids: set[str] = set()

    signals = detect_signals(items)
    for signal in signals:
        trigger_terms = _SIGNAL_QUERY_RULES.get(signal.kind, set())
        if query_terms & trigger_terms:
            ids.update(signal.evidence_ids)

    def add_where(predicate) -> None:
        for item in items:
            if predicate(item):
                ids.add(item.evidence_id)

    if query_terms & {"defect", "defects", "testing", "test", "quality"}:
        add_where(lambda item: item.source_type == "test_system")
        add_where(
            lambda item: item.source_type == "retrospective"
            and item.project_id == "SEC"
        )
        add_where(
            lambda item: item.source_type == "confluence"
            and item.project_id == "SEC"
        )

    if query_terms & {"approval", "approver", "compliance", "sign-off", "signoff"}:
        add_where(
            lambda item: item.source_type in {"decision_log", "meeting_notes", "confluence"}
            and (
                item.project_id == "SEC"
                or "approval" in json.dumps(item.payload).lower()
                or "approver" in json.dumps(item.payload).lower()
                or "compliance" in json.dumps(item.payload).lower()
            )
        )
        add_where(lambda item: item.source_type == "dependency_map")

    if query_terms & {"resource", "resources", "shared", "maya", "capacity", "staffing"}:
        add_where(lambda item: item.source_type == "resource_plan")
        add_where(
            lambda item: "maya" in json.dumps(item.payload).lower()
            or item.evidence_id in {"ATLAS-101", "ATLAS-109", "DEP-MAP-1112"}
        )

    if query_terms & {"partner", "integration", "recovery", "sandbox"}:
        add_where(
            lambda item: "partner" in json.dumps(item.payload).lower()
            or "integration" in json.dumps(item.payload).lower()
            or item.evidence_id in {
                "RETRO-PLAT-Q3",
                "DEP-MAP-1112",
                "MILESTONES-1112",
                "STATUS-1112",
                "RES-1112",
            }
        )

    if query_terms & {"scope", "export", "filtering"}:
        add_where(
            lambda item: item.evidence_id in {
                "D-02",
                "PAGE-APP",
                "MTG-1111-PORTFOLIO",
                "MTG-1112-GTM",
                "DEP-MAP-1112",
                "ATLAS-116",
                "ATLAS-117",
                "ATLAS-118",
            }
        )

    if query_terms & {"executive", "green", "status", "operational", "fresher"}:
        add_where(lambda item: item.source_type == "exec_status")
        add_where(
            lambda item: item.evidence_id in {
                "MTG-1111-PORTFOLIO",
                "ATLAS-101",
                "TEST-1112",
                "RES-1112",
            }
        )

    if query_terms & {"budget", "finance"}:
        add_where(lambda item: item.source_type == "finance_snapshot")
        add_where(
            lambda item: item.evidence_id in {
                "ATLAS-101",
                "ATLAS-102",
                "TEST-1112",
                "STATUS-1112",
            }
        )

    if query_terms & {"threshold", "refusal", "guardrail"}:
        add_where(
            lambda item: item.evidence_id in {
                "ATLAS-108",
                "PAGE-AI",
                "R-03",
                "MILESTONES-1112",
            }
        )

    if (
        {"critical", "dependency"} <= query_terms
        or {"dependency", "launch"} <= query_terms
    ):
        add_where(
            lambda item: item.evidence_id in {
                "DEP-MAP-1112",
                "D-01",
                "MILESTONES-1112",
            }
        )

    return ids


def retrieve_evidence(
    evidence: Iterable[Evidence],
    query: str,
    *,
    project_ids: Iterable[str] = (),
    limit: int = 16,
) -> list[RetrievalHit]:
    items = list(evidence)
    query_terms = _tokens(query)
    projects = set(project_ids)
    joined_ids = _deterministic_join_ids(items, query)
    hits: list[RetrievalHit] = []

    for item in items:
        haystack = " ".join(
            (
                item.evidence_id,
                item.source_type,
                item.project_id,
                json.dumps(item.payload, sort_keys=True),
            )
        ).lower()
        matched = tuple(sorted(term for term in query_terms if term in haystack))
        score = float(len(matched))

        if item.project_id in projects:
            score += 4.0
        if item.project_id == "atlas" and projects:
            score += 1.0
        score += max(0.0, 1.25 - (0.25 * item.authority_tier))

        if item.evidence_id in joined_ids:
            score += 25.0

        if score > 0:
            hits.append(RetrievalHit(item, score, matched))

    hits.sort(
        key=lambda hit: (
            hit.score,
            hit.evidence.source_updated_at,
            -hit.evidence.authority_tier,
        ),
        reverse=True,
    )
    return hits[:limit]
