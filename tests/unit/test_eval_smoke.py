from pathlib import Path

from program_os.evals.smoke import run_signal_smoke


def test_offline_signal_smoke_passes():
    result = run_signal_smoke(Path("examples/atlas/data"))
    assert result["passed"] is True
    assert result["evidence_count"] == 48
