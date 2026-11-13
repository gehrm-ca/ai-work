"""Offline evaluation smoke checks that do not call a model."""
from __future__ import annotations

from pathlib import Path

from program_os.evidence import load_evidence_dir
from program_os.signals import detect_signals

EXPECTED_SIGNAL_KINDS = {
    "cross_source_date_conflict",
    "resource_overallocation",
    "worsening_defect_trend",
    "approval_timing_risk",
    "launch_threshold_gap",
    "unapproved_scope_change",
    "official_status_lag",
}


def run_signal_smoke(data_dir: Path) -> dict:
    evidence = load_evidence_dir(data_dir)
    detected = {signal.kind for signal in detect_signals(evidence)}
    missing = sorted(EXPECTED_SIGNAL_KINDS.difference(detected))
    return {
        "evidence_count": len(evidence),
        "expected_signal_count": len(EXPECTED_SIGNAL_KINDS),
        "detected_expected_signals": len(EXPECTED_SIGNAL_KINDS) - len(missing),
        "missing_signals": missing,
        "passed": not missing,
    }
