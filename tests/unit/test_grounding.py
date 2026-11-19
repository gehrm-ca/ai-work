import json
from datetime import datetime, timezone

import pytest

from program_os.agent import AgentAssessmentDraft, build_agent, render_evidence
from program_os.confidence import ConfidenceInputs
from program_os.controls import ControlContext
from program_os.grounding import GroundingError, finalize_assessment
from program_os.models import Evidence, Rag, Trend


def evidence_item() -> Evidence:
    return Evidence(
        evidence_id="E-1",
        source_type="jira",
        source_id="E-1",
        project_id="PLAT",
        source_updated_at=datetime.now(timezone.utc),
        retrieved_at=datetime.now(timezone.utc),
        authority_tier=1,
        payload={"status": "Blocked"},
    )


def test_unknown_citation_is_rejected():
    draft = AgentAssessmentDraft(
        proposed_rag=Rag.GREEN,
        trend=Trend.STABLE,
        conclusion="Looks fine.",
        cited_evidence_ids=["NOT-IN-CONTEXT"],
    )
    with pytest.raises(GroundingError):
        finalize_assessment(
            draft,
            project_id="PLAT",
            official_rag=Rag.GREEN,
            evidence=[evidence_item()],
            controls=ControlContext(),
            confidence_inputs=ConfidenceInputs(0.9, 0.9, 0.9, 0.9, 0.9),
        )


def test_hard_gate_overrides_model_green():
    draft = AgentAssessmentDraft(
        proposed_rag=Rag.GREEN,
        trend=Trend.STABLE,
        conclusion="Schedule is otherwise healthy.",
        cited_evidence_ids=["E-1"],
    )
    result = finalize_assessment(
        draft,
        project_id="PLAT",
        official_rag=Rag.GREEN,
        evidence=[evidence_item()],
        controls=ControlContext(unresolved_launch_critical_blocker=True),
        confidence_inputs=ConfidenceInputs(0.9, 0.9, 0.9, 0.9, 0.9),
    )
    assert result.forecast_rag == Rag.RED
    assert result.hard_gates[0].code == "launch_critical_blocker"


def test_agent_is_single_agent_with_structured_output():
    agent = build_agent()
    assert agent.name == "Program OS Analyst"
    assert agent.handoffs == []
    assert agent.output_type is AgentAssessmentDraft


def test_resolved_historical_contradiction_does_not_force_amber():
    draft = AgentAssessmentDraft(
        proposed_rag=Rag.GREEN,
        trend=Trend.STABLE,
        conclusion="Approved scope removal resolves the issue.",
        contradictions=["Historical source still shows the pre-approval state."],
        cited_evidence_ids=["E-1"],
    )
    result = finalize_assessment(
        draft,
        project_id="APP",
        official_rag=Rag.GREEN,
        evidence=[evidence_item()],
        controls=ControlContext(),
        confidence_inputs=ConfidenceInputs(0.9, 0.9, 0.9, 0.9, 0.9),
        authoritative_conflict_resolved=True,
    )
    assert result.forecast_rag == Rag.GREEN
    assert result.hard_gates == []


def test_model_context_excludes_connector_permission_metadata():
    item = evidence_item().model_copy(
        update={
            "payload": {
                "status": "Blocked",
                "_connector": {
                    "connector_id": "jira-live",
                    "source_url": "https://customer.example.invalid/browse/SECRET-1",
                    "permission_context": {
                        "principal": "person@example.invalid",
                        "scopes": ["read:jira-work"],
                    },
                },
            }
        }
    )

    rendered = json.loads(render_evidence([item]))

    assert rendered[0]["payload"] == {"status": "Blocked"}
    assert "person@example.invalid" not in json.dumps(rendered)
    assert "customer.example.invalid" not in json.dumps(rendered)
