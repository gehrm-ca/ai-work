from pathlib import Path

from program_os.evidence import load_evidence_dir
from program_os.signals import detect_signals


def test_atlas_planted_signals_are_detected():
    evidence = load_evidence_dir(Path("examples/atlas/data"))
    kinds = {signal.kind for signal in detect_signals(evidence)}
    assert {
        "resource_overallocation",
        "worsening_defect_trend",
        "unapproved_scope_change",
        "cross_source_date_conflict",
        "launch_threshold_gap",
        "approval_timing_risk",
        "official_status_lag",
    }.issubset(kinds)
