from pathlib import Path
import json

from program_os.showcase import export_showcase


def test_showcase_export_uses_deterministic_demo_payload(tmp_path):
    output = tmp_path / "atlas-demo.json"
    payload = export_showcase(output)

    assert output.exists()
    written = json.loads(output.read_text(encoding="utf-8"))
    assert written["evidence_count"] == 48
    assert written["friday_status"]["official_rag"] == "GREEN"
    assert written["friday_status"]["forecast_rag"] == "AMBER"
    assert len(written["monday_actions"]) >= 1
    assert written["signals"]
    assert payload["evidence_count"] == written["evidence_count"]
