from datetime import date

from program_os.controls import ControlContext, evaluate_hard_gates
from program_os.models import Rag


def test_missing_mandatory_approval_prevents_green():
    result = evaluate_hard_gates(
        Rag.GREEN,
        ControlContext(mandatory_approval_required=True, mandatory_approval_verified=False),
    )
    assert result.constrained_rag == Rag.AMBER
    assert result.findings[0].code == "mandatory_approval_not_verified"


def test_launch_critical_blocker_forces_red():
    result = evaluate_hard_gates(
        Rag.GREEN,
        ControlContext(unresolved_launch_critical_blocker=True),
    )
    assert result.constrained_rag == Rag.RED


def test_dependency_after_launch_without_mitigation_forces_red():
    result = evaluate_hard_gates(
        Rag.AMBER,
        ControlContext(
            critical_dependency_forecast_date=date(2026, 12, 6),
            committed_launch_date=date(2026, 12, 4),
            viable_mitigation=False,
        ),
    )
    assert result.constrained_rag == Rag.RED


def test_authoritative_conflict_blocks_green():
    result = evaluate_hard_gates(Rag.GREEN, ControlContext(authoritative_conflict=True))
    assert result.constrained_rag == Rag.AMBER


def test_no_gate_leaves_proposed_status_unchanged():
    result = evaluate_hard_gates(Rag.GREEN, ControlContext())
    assert result.constrained_rag == Rag.GREEN
    assert result.findings == ()
