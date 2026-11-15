from datetime import date

from program_os.evals.live import (
    EvalOutput,
    _controls,
    _semantic_phrase_present,
    _unsupported_assertion_present,
    score_case,
)
from program_os.models import ConfidenceBand, Rag


def test_scenario_overrides_create_hard_gate_context():
    context = _controls({
        "scenario_overrides": {
            "critical_dependency_forecast_date": "2026-12-06",
            "viable_mitigation": False,
        }
    })
    assert context.critical_dependency_forecast_date == date(2026, 12, 6)
    assert context.committed_launch_date == date(2026, 12, 4)
    assert context.viable_mitigation is False


def test_score_case_detects_missing_required_citation():
    case = {
        "id": "E",
        "expected": {
            "forecast_rag": "AMBER",
            "confidence": "Moderate",
            "must_cite": ["E-1"],
            "must_not_assert": [],
            "insufficient_evidence": False,
        },
    }
    output = EvalOutput(
        forecast_rag=Rag.AMBER,
        confidence=ConfidenceBand.MODERATE,
        conclusion="Material risk exists.",
        cited_evidence_ids=[],
    )
    failures = score_case(case, output, {"E-1"})
    assert any(failure.kind == "incorrect_evidence_citation" for failure in failures)


def test_score_case_marks_unknown_evidence_catastrophic():
    case = {
        "id": "E",
        "expected": {
            "must_cite": [],
            "must_not_assert": [],
            "insufficient_evidence": False,
        },
    }
    output = EvalOutput(
        forecast_rag=Rag.AMBER,
        confidence=ConfidenceBand.MODERATE,
        conclusion="Risk.",
        cited_evidence_ids=["MADE-UP"],
    )
    failures = score_case(case, output, {"REAL"})
    assert any(failure.kind == "fabricated_material_evidence" for failure in failures)


def test_semantic_matching_handles_program_management_synonyms():
    assert _semantic_phrase_present(
        "Active work exists for scope that is not formally committed",
        "Implementation is already scheduled even though the scope is not approved.",
    )
    assert _semantic_phrase_present(
        "Reallocate or sequence Maya's work",
        "Prioritize Maya on Platform and reassign her AI support.",
    )


def test_forbidden_assertion_does_not_match_explicit_negation():
    assert not _unsupported_assertion_present(
        "Export filtering is approved launch scope",
        "Export filtering is not approved launch scope.",
    )


def test_cannot_green_case_accepts_amber_or_red():
    case = {
        "id": "E",
        "expected": {
            "forecast_rag": "AMBER",
            "allowed_forecast_rags": ["AMBER", "RED"],
            "confidence": "Low",
            "hard_gate": "cannot_green",
            "must_cite": [],
            "must_not_assert": [],
            "insufficient_evidence": False,
        },
    }
    output = EvalOutput(
        forecast_rag=Rag.RED,
        confidence=ConfidenceBand.LOW,
        conclusion="Approval not verified.",
    )
    failures = score_case(case, output, set())
    assert not any(failure.kind == "incorrect_hard_gate" for failure in failures)
