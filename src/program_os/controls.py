"""Deterministic RAG controls.

These rules constrain model judgment. The model may explain or add context, but
it may not bypass a hard gate.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .models import Rag


_RAG_SEVERITY = {
    Rag.GREEN: 0,
    Rag.UNKNOWN: 1,
    Rag.AMBER: 2,
    Rag.RED: 3,
}


@dataclass(frozen=True)
class ControlContext:
    mandatory_approval_required: bool = False
    mandatory_approval_verified: bool | None = None
    unresolved_launch_critical_blocker: bool = False
    critical_dependency_forecast_date: date | None = None
    committed_launch_date: date | None = None
    viable_mitigation: bool = True
    material_required_evidence_missing: bool = False
    authoritative_conflict: bool = False


@dataclass(frozen=True)
class GateFinding:
    code: str
    rag: Rag
    reason: str


@dataclass(frozen=True)
class GateResult:
    constrained_rag: Rag
    findings: tuple[GateFinding, ...]


def worse_of(left: Rag, right: Rag) -> Rag:
    return left if _RAG_SEVERITY[left] >= _RAG_SEVERITY[right] else right


def evaluate_hard_gates(proposed_rag: Rag, context: ControlContext) -> GateResult:
    result = proposed_rag
    findings: list[GateFinding] = []

    if context.unresolved_launch_critical_blocker:
        findings.append(GateFinding(
            "launch_critical_blocker",
            Rag.RED,
            "An unresolved launch-critical blocker requires RED.",
        ))
        result = worse_of(result, Rag.RED)

    if (
        context.critical_dependency_forecast_date
        and context.committed_launch_date
        and context.critical_dependency_forecast_date > context.committed_launch_date
        and not context.viable_mitigation
    ):
        findings.append(GateFinding(
            "critical_dependency_after_launch",
            Rag.RED,
            "A critical dependency is forecast after launch with no viable mitigation.",
        ))
        result = worse_of(result, Rag.RED)

    if context.mandatory_approval_required and context.mandatory_approval_verified is not True:
        findings.append(GateFinding(
            "mandatory_approval_not_verified",
            Rag.AMBER,
            "A mandatory approval is not verified; status cannot be GREEN.",
        ))
        result = worse_of(result, Rag.AMBER)

    if context.material_required_evidence_missing:
        findings.append(GateFinding(
            "material_evidence_missing",
            Rag.AMBER,
            "Material required evidence is missing; status cannot be confidently GREEN.",
        ))
        result = worse_of(result, Rag.AMBER)

    if context.authoritative_conflict:
        findings.append(GateFinding(
            "authoritative_evidence_conflict",
            Rag.AMBER,
            "Authoritative evidence conflicts; ground truth must be established.",
        ))
        result = worse_of(result, Rag.AMBER)

    return GateResult(constrained_rag=result, findings=tuple(findings))
