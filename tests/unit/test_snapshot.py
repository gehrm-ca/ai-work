from pathlib import Path

from program_os.snapshot import build_atlas_snapshot


def test_snapshot_produces_portfolio_tradeoff():
    snapshot = build_atlas_snapshot(Path("examples/atlas/data"))
    assert snapshot["evidence_count"] == 48
    assert snapshot["recommendation"] is not None
    assert snapshot["recommendation"]["approval_required"] is True
    assert snapshot["recommendation"]["downstream_consequences"]
