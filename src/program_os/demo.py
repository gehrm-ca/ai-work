"""Monday/Friday operating-loop outputs for the Atlas V2 demo."""
from __future__ import annotations

import json
from datetime import date
from pathlib import Path
from typing import Iterable

from pydantic import BaseModel, Field

from .evidence import load_evidence_dir
from .models import ConfidenceBand, Rag, Trend
from .priority import PriorityInputs, intervention_priority
from .recommendation import recommend_resource_tradeoff
from .signals import Signal, detect_signals


class MondayAction(BaseModel):
    action_id: str
    issue_or_risk: str
    project_id: str
    impact: str
    probability: str
    next_step: str
    escalation: str
    priority_score: float = Field(ge=0, le=1)
    evidence_ids: list[str]


class FridayStatus(BaseModel):
    portfolio_id: str
    official_rag: Rag
    forecast_rag: Rag
    confidence: ConfidenceBand
    trend: Trend
    launch_date: date
    top_risks: list[str]
    contradictions: list[str]
    next_milestone: str
    budget_tracking: str
    summary: str


_ACTION_CONFIG = {
    "cross_source_date_conflict": {
        "criticality": 1.0, "probability": 0.8, "impact": 0.9, "time": 0.9,
        "impact_label": "High", "probability_label": "High",
        "next_step": "Establish ground truth for the partner-integration completion date and update the critical-path baseline.",
        "escalation": "Monday Action",
    },
    "resource_overallocation": {
        "criticality": 1.0, "probability": 0.8, "impact": 0.9, "time": 0.9,
        "impact_label": "High", "probability_label": "High",
        "next_step": "Resolve Maya's competing PLAT/AI commitments and document the downstream milestone tradeoff.",
        "escalation": "Monday Action",
    },
    "worsening_defect_trend": {
        "criticality": 0.9, "probability": 0.85, "impact": 0.9, "time": 0.85,
        "impact_label": "High", "probability_label": "High",
        "next_step": "Review defect drivers, regression capacity, and whether the current security/test recovery plan remains credible.",
        "escalation": "Monday Action",
    },
    "approval_timing_risk": {
        "criticality": 0.9, "probability": 0.65, "impact": 0.9, "time": 0.75,
        "impact_label": "High", "probability_label": "Medium",
        "next_step": "Confirm a backup compliance approver or move the evidence-review decision earlier.",
        "escalation": "Monday Action",
    },
    "launch_threshold_gap": {
        "criticality": 0.9, "probability": 0.7, "impact": 0.8, "time": 0.75,
        "impact_label": "High", "probability_label": "Medium",
        "next_step": "Close or explicitly disposition the refusal-test gap against the documented launch threshold.",
        "escalation": "Monday Action",
    },
    "unapproved_scope_change": {
        "criticality": 0.8, "probability": 0.8, "impact": 0.8, "time": 0.7,
        "impact_label": "High", "probability_label": "High",
        "next_step": "Reconcile export-filtering implementation with the pending scope decision and stakeholder commitments.",
        "escalation": "Monday Action",
    },
    "official_status_lag": {
        "criticality": 0.9, "probability": 0.75, "impact": 0.85, "time": 0.8,
        "impact_label": "High", "probability_label": "High",
        "next_step": "Revalidate the official GREEN against fresher operational evidence before the next executive status is issued.",
        "escalation": "Monday Action",
    },
}


def build_monday_actions(signals: Iterable[Signal]) -> list[MondayAction]:
    actions: list[MondayAction] = []
    for index, signal in enumerate(signals, start=1):
        config = _ACTION_CONFIG.get(signal.kind)
        if not config:
            continue
        score = intervention_priority(PriorityInputs(
            config["criticality"],
            config["probability"],
            config["impact"],
            config["time"],
        ))
        actions.append(MondayAction(
            action_id=f"MON-{index:02d}",
            issue_or_risk=signal.summary,
            project_id=signal.project_id,
            impact=config["impact_label"],
            probability=config["probability_label"],
            next_step=config["next_step"],
            escalation=config["escalation"],
            priority_score=round(score, 4),
            evidence_ids=list(signal.evidence_ids),
        ))
    return sorted(actions, key=lambda item: item.priority_score, reverse=True)


def _latest_payload(evidence, source_type: str) -> dict:
    matches = [item for item in evidence if item.source_type == source_type]
    if not matches:
        return {}
    latest = max(matches, key=lambda item: item.source_updated_at)
    return latest.payload


def build_friday_status(data_dir: Path) -> FridayStatus:
    evidence = load_evidence_dir(data_dir)
    signals = detect_signals(evidence)
    portfolio = json.loads((data_dir / "portfolio.json").read_text(encoding="utf-8"))

    status = _latest_payload(evidence, "exec_status")
    budget = _latest_payload(evidence, "finance_snapshot")
    milestone_payload = _latest_payload(evidence, "project_plan")
    milestones = sorted(
        milestone_payload.get("milestones", []),
        key=lambda item: item["date"],
    )

    top = [
        signal.summary for signal in signals
        if signal.kind != "official_status_lag"
    ][:5]
    contradictions = [
        signal.summary for signal in signals
        if signal.kind in {
            "cross_source_date_conflict",
            "unapproved_scope_change",
            "official_status_lag",
        }
    ]

    return FridayStatus(
        portfolio_id=portfolio["portfolio_id"],
        official_rag=Rag(status.get("portfolio_rag", "UNKNOWN")),
        forecast_rag=Rag.AMBER if signals else Rag.GREEN,
        confidence=ConfidenceBand.MODERATE if contradictions else ConfidenceBand.HIGH,
        trend=Trend.DETERIORATING if any(
            signal.kind == "worsening_defect_trend" for signal in signals
        ) else Trend.STABLE,
        launch_date=date.fromisoformat(portfolio["target_launch_date"]),
        top_risks=top,
        contradictions=contradictions,
        next_milestone=(
            f'{milestones[0]["name"]} — {milestones[0]["date"]}'
            if milestones else "Unknown"
        ),
        budget_tracking=(
            f'{budget.get("budget_status", "Unknown")}; forecast variance '
            f'{budget.get("forecast_variance_pct", "unknown")}%'
        ),
        summary=(
            "Official reporting remains GREEN, but forecast is AMBER because fresher "
            "operational evidence shows dependency, resource, quality, scope, and "
            "approval risks that require intervention."
        ),
    )


def build_demo_payload(data_dir: Path) -> dict:
    evidence = load_evidence_dir(data_dir)
    signals = detect_signals(evidence)
    recommendation = recommend_resource_tradeoff(signals, evidence)
    return {
        "evidence_count": len(evidence),
        "monday_actions": [
            item.model_dump(mode="json") for item in build_monday_actions(signals)
        ],
        "signals": [
            {
                "kind": item.kind,
                "project_id": item.project_id,
                "severity": item.severity,
                "summary": item.summary,
                "evidence_ids": list(item.evidence_ids),
            }
            for item in signals
        ],
        "recommendation": (
            recommendation.model_dump(mode="json") if recommendation else None
        ),
        "friday_status": build_friday_status(data_dir).model_dump(mode="json"),
    }
