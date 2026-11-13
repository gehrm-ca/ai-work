from program_os.evals.scoring import EvalFailure, summarize_failures


def test_weighted_penalty():
    result = summarize_failures([
        EvalFailure("missed_critical_risk", "E01"),
        EvalFailure("extra_low_severity_alert", "E02"),
    ])
    assert result.weighted_penalty == 6
    assert result.catastrophic is False


def test_catastrophic_gate_is_independent_of_score():
    result = summarize_failures([
        EvalFailure("fabricated_material_evidence", "E03"),
    ])
    assert result.catastrophic is True
    assert result.catastrophic_failures[0].case_id == "E03"
