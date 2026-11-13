"""Ground and constrain model-produced assessments."""
from __future__ import annotations

from dataclasses import replace
from datetime import datetime, timezone
from typing import Callable, Iterable
from uuid import uuid4

from .agent import AgentAssessmentDraft
from .confidence import ConfidenceInputs, calculate_confidence
from .controls import ControlContext, evaluate_hard_gates
from .models import Assessment, Evidence, HardGate, Rag
from .retrieval import retrieve_evidence


class GroundingError(ValueError):
    pass


def validate_citations(draft: AgentAssessmentDraft, evidence: Iterable[Evidence]) -> None:
    available = {item.evidence_id for item in evidence}
    cited = set(draft.cited_evidence_ids)
    unknown = cited.difference(available)
    if unknown:
        raise GroundingError(f"Assessment cites evidence not in context: {sorted(unknown)}")
    if not cited:
        raise GroundingError("Material assessment must cite at least one evidence item.")


def finalize_assessment(
    draft: AgentAssessmentDraft,
    *,
    project_id: str,
    official_rag: Rag,
    evidence: Iterable[Evidence],
    controls: ControlContext,
    confidence_inputs: ConfidenceInputs,
    system_version: str = "0.2.0",
) -> Assessment:
    evidence = list(evidence)
    validate_citations(draft, evidence)

    if draft.contradictions and not controls.authoritative_conflict:
        controls = replace(controls, authoritative_conflict=True)

    gate = evaluate_hard_gates(draft.proposed_rag, controls)
    confidence = calculate_confidence(confidence_inputs)

    return Assessment(
        assessment_id=f"asmt-{uuid4().hex[:12]}",
        project_id=project_id,
        official_rag=official_rag,
        forecast_rag=gate.constrained_rag,
        confidence=confidence.band,
        trend=draft.trend,
        conclusion=draft.conclusion,
        evidence_ids=draft.cited_evidence_ids,
        contradictions=draft.contradictions,
        assumptions=draft.assumptions + (
            [f"Missing information: {item}" for item in draft.missing_information]
        ),
        hard_gates=[
            HardGate(code=item.code, reason=item.reason, rag_floor=item.rag)
            for item in gate.findings
        ],
        system_version=system_version,
        created_at=datetime.now(timezone.utc),
    )


def assess_question(
    question: str,
    *,
    project_id: str,
    official_rag: Rag,
    evidence: Iterable[Evidence],
    controls: ControlContext,
    confidence_inputs: ConfidenceInputs,
    runner: Callable[[str, Iterable[Evidence]], AgentAssessmentDraft],
    retrieval_limit: int = 12,
) -> Assessment:
    evidence = list(evidence)
    hits = retrieve_evidence(
        evidence,
        question,
        project_ids=(() if project_id == "atlas" else (project_id,)),
        limit=retrieval_limit,
    )
    context = [hit.evidence for hit in hits]
    draft = runner(question, context)
    return finalize_assessment(
        draft,
        project_id=project_id,
        official_rag=official_rag,
        evidence=context,
        controls=controls,
        confidence_inputs=confidence_inputs,
    )
