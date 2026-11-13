from program_os.priority import PriorityInputs, intervention_priority


def test_priority_uses_four_primary_factors():
    score = intervention_priority(PriorityInputs(1.0, 0.8, 0.9, 0.75))
    assert round(score, 3) == 0.54


def test_confidence_can_modify_priority():
    full = intervention_priority(PriorityInputs(1, 1, 1, 1, 1))
    reduced = intervention_priority(PriorityInputs(1, 1, 1, 1, 0.5))
    assert reduced < full
