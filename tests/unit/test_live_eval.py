from datetime import date

from program_os.evals.live import EvalOutput, _controls, score_case
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
