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


def _date_conflict(evidence):
    return next(
        (s for s in detect_signals(evidence) if s.kind == "cross_source_date_conflict"),
        None,
    )


def test_date_conflict_names_only_dates_stated_for_the_partner_integration():
    evidence = load_evidence_dir(Path("examples/atlas/data"))
    signal = _date_conflict(evidence)
    assert signal is not None
    assert signal.summary == (
        "Partner integration dates conflict across current sources: "
        "2026-11-14 (PAGE-PLAT), "
        "2026-11-18 (ATLAS-101, MILESTONES-1112), "
        "2026-11-20 (MTG-1111-PORTFOLIO)."
    )


def test_date_conflict_leaves_out_dates_that_belong_to_other_work():
    evidence = load_evidence_dir(Path("examples/atlas/data"))
    summary = _date_conflict(evidence).summary
    # Other milestones in the plan, dependency need-by dates and the launch date
    # sit in records that mention the partner integration but are not its dates.
    for unrelated in (
        "2026-11-19", "2026-11-21", "2026-11-22", "2026-11-24",
        "2026-11-25", "2026-11-27", "2026-12-03", "2026-12-04",
    ):
        assert unrelated not in summary


def test_no_date_conflict_when_only_one_date_is_stated_for_the_integration():
    evidence = load_evidence_dir(Path("examples/atlas/data"))
    # The milestone plan and dependency map hold a dozen dates between them,
    # but only one is the partner integration's own date.
    subset = [
        item for item in evidence
        if item.evidence_id in {"MILESTONES-1112", "DEP-MAP-1112", "STATUS-1112"}
    ]
    assert len(subset) == 3
    assert _date_conflict(subset) is None


def test_date_conflict_still_cites_every_partner_integration_record():
    evidence = load_evidence_dir(Path("examples/atlas/data"))
    assert set(_date_conflict(evidence).evidence_ids) == {
        "ATLAS-101", "PAGE-PLAT", "MTG-1111-PORTFOLIO", "RETRO-PLAT-Q3",
        "STATUS-1112", "DEP-MAP-1112", "MILESTONES-1112",
    }


def test_detected_signals_expose_reasoning_and_change_conditions():
    evidence = load_evidence_dir(Path("examples/atlas/data"))
    signals = detect_signals(evidence)

    assert signals
    assert all(signal.reasoning_factors for signal in signals)
    assert all(signal.what_would_change for signal in signals)

    date_conflict = next(
        signal for signal in signals if signal.kind == "cross_source_date_conflict"
    )
    assert "incompatible completion dates" in date_conflict.reasoning_factors[0]
    assert "converges on one partner-integration completion date" in date_conflict.what_would_change[0]
