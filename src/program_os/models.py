"""Canonical Program OS domain models.

Evidence observations are immutable. Assessments, recommendations, overrides,
and learning proposals are new versioned records rather than mutations of evidence.
"""
from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class Rag(str, Enum):
    GREEN = "GREEN"
    AMBER = "AMBER"
    RED = "RED"
    UNKNOWN = "UNKNOWN"


class ConfidenceBand(str, Enum):
    HIGH = "High"
    MODERATE = "Moderate"
    LOW = "Low"


class Trend(str, Enum):
    IMPROVING = "improving"
    STABLE = "stable"
    DETERIORATING = "deteriorating"


class Evidence(BaseModel):
    model_config = ConfigDict(frozen=True)

    evidence_id: str
    source_type: str
    source_id: str
    project_id: str
    source_updated_at: datetime
    retrieved_at: datetime
    authority_tier: int = Field(ge=1, le=5)
    payload: dict[str, Any]


class Portfolio(BaseModel):
    portfolio_id: str
    name: str
    target_launch_date: date | None = None


class Project(BaseModel):
    project_id: str
    portfolio_id: str
    name: str
    official_rag: Rag = Rag.UNKNOWN
    launch_date: date | None = None
    strategic_priority: int = Field(default=3, ge=1, le=5)


class Milestone(BaseModel):
    milestone_id: str
    project_id: str
    name: str
    date: date
    critical: bool = False


class WorkItem(BaseModel):
    work_item_id: str
    project_id: str
    title: str
    status: str
    due_date: date | None = None
    critical_path: bool = False


class Dependency(BaseModel):
    dependency_id: str
    from_ref: str
    to_ref: str
    required_by: date | None = None
    critical: bool = False


class Risk(BaseModel):
    risk_id: str
    project_id: str
    title: str
    probability: str
    impact: str
    status: str
    owner: str | None = None
    trend: Trend = Trend.STABLE


class Issue(BaseModel):
    issue_id: str
    project_id: str
    title: str
    severity: str
    status: str


class ScopeItem(BaseModel):
    scope_item_id: str
    project_id: str
    title: str
    state: str


class Change(BaseModel):
    change_id: str
    project_id: str
    change_type: str
    status: str
    description: str


class Decision(BaseModel):
    decision_id: str
    project_id: str
    title: str
    status: str
    authority: str
    decision: str | None = None


class Stakeholder(BaseModel):
    stakeholder_id: str
    name: str
    role: str
    authority: str | None = None


class Resource(BaseModel):
    resource_id: str
    name: str
    role: str
    allocations: dict[str, float] = Field(default_factory=dict)


class QualitySignal(BaseModel):
    signal_id: str
    project_id: str
    signal_type: str
    value: Any
    observed_at: datetime


class Action(BaseModel):
    action_id: str
    project_id: str
    title: str
    impact: str
    probability: str
    next_step: str
    evidence_ids: list[str] = Field(default_factory=list)


class HardGate(BaseModel):
    code: str
    reason: str
    rag_floor: Rag


class Assessment(BaseModel):
    assessment_id: str
    project_id: str
    official_rag: Rag
    forecast_rag: Rag
    confidence: ConfidenceBand
    trend: Trend
    conclusion: str
    evidence_ids: list[str]
    contradictions: list[str] = Field(default_factory=list)
    assumptions: list[str] = Field(default_factory=list)
    hard_gates: list[HardGate] = Field(default_factory=list)
    system_version: str
    created_at: datetime


class Recommendation(BaseModel):
    recommendation_id: str
    project_id: str
    action: str
    expected_benefit: str
    downstream_consequences: list[str]
    confidence: ConfidenceBand
    evidence_ids: list[str]
    approval_required: bool = True
    system_version: str


class Override(BaseModel):
    override_id: str
    recommendation_id: str | None = None
    assessment_id: str | None = None
    actor: str
    new_status: Rag | None = None
    rationale: str
    missed_context: str | None = None
    exception_type: str
    expected_consequence_if_wrong: str | None = None
    created_at: datetime


class AuditEvent(BaseModel):
    event_id: str
    actor: str
    event_type: str
    entity_type: str
    entity_id: str
    before: dict[str, Any] | None = None
    after: dict[str, Any] | None = None
    created_at: datetime


class LearningProposal(BaseModel):
    proposal_id: str
    triggering_case_ids: list[str]
    failure_category: str
    root_cause_hypothesis: str
    proposed_change: str
    expected_improvement: str
    possible_regressions: list[str]
    evaluation_result: str | None = None
    approver: str | None = None
    approved: bool = False
    effective_version: str | None = None
    rollback: str | None = None
