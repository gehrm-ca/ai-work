import json
import subprocess
import sys
from datetime import datetime, timedelta, timezone

from program_os.adapters import (
    IngestionBatch,
    PermissionContext,
    SourceRecord,
)
from program_os.models import ConfidenceBand, Rag
from program_os.pilot import (
    PilotBaseline,
    PilotEvidenceSnapshot,
    PilotRecord,
)
from program_os.readiness import assess_evidence_readiness


NOW = datetime(2026, 11, 16, 20, 0, tzinfo=timezone.utc)


def source_record(
    source_id: str,
    *,
    source_type: str,
    project_id: str,
) -> SourceRecord:
    return SourceRecord(
        source_type=source_type,
        source_id=source_id,
        project_id=project_id,
        source_updated_at=NOW - timedelta(hours=4),
        authority_tier=1,
        payload={"summary": "Private pilot content."},
        permission_context=PermissionContext(
            principal="pilot-user",
            scopes=("read",),
            visibility="source-filtered",
        ),
    )


def pilot_record() -> PilotRecord:
    return PilotRecord(
        pilot_id="pilot-command-test",
        program_alias="Program A",
        started_at=NOW,
        baseline=PilotBaseline(
            recorded_at=NOW,
            official_rag=Rag.GREEN,
            forecast_expectation="On track.",
            plan_confidence=ConfidenceBand.MODERATE,
        ),
        evidence_snapshot=PilotEvidenceSnapshot(
            snapshot_id="snapshot-1",
            captured_at=NOW,
            source_types=("jira", "risk_log"),
            evidence_count=2,
            private_location="var/pilots/private-evidence/",
        ),
    )


def run_packet(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "scripts/pilot_packet.py", *args],
        check=False,
        capture_output=True,
        text=True,
    )


def test_attach_readiness_then_check_ready_opens_full_pilot_gate(tmp_path):
    pilot_path = tmp_path / "pilot.json"
    pilot_path.write_text(pilot_record().model_dump_json(indent=2), encoding="utf-8")

    batch = IngestionBatch(
        connector_id="pilot-bundle",
        retrieved_at=NOW,
        records=(
            source_record("JIRA-1", source_type="jira", project_id="A"),
            source_record("RISK-1", source_type="risk_log", project_id="B"),
        ),
    )
    readiness = assess_evidence_readiness(batch)
    readiness_path = tmp_path / "readiness.json"
    readiness_path.write_text(
        json.dumps({"evidence_readiness": readiness.model_dump(mode="json")}),
        encoding="utf-8",
    )

    attached = run_packet("attach-readiness", str(pilot_path), str(readiness_path))
    assert attached.returncode == 0, attached.stderr
    assert json.loads(attached.stdout)["ready_for_analysis"] is True

    checked = run_packet("check-ready", str(pilot_path))
    assert checked.returncode == 0, checked.stderr
    output = json.loads(checked.stdout)
    assert output == {
        "ready_for_analysis": True,
        "readiness_level": "pilot_candidate",
    }


def test_connector_ready_snapshot_does_not_open_full_pilot_gate(tmp_path):
    pilot_path = tmp_path / "pilot.json"
    pilot_path.write_text(pilot_record().model_dump_json(indent=2), encoding="utf-8")

    batch = IngestionBatch(
        connector_id="jira-cloud",
        retrieved_at=NOW,
        records=(
            source_record("JIRA-1", source_type="jira", project_id="A"),
            source_record("JIRA-2", source_type="jira", project_id="B"),
        ),
    )
    readiness = assess_evidence_readiness(batch)
    readiness_path = tmp_path / "readiness.json"
    readiness_path.write_text(
        json.dumps(readiness.model_dump(mode="json")),
        encoding="utf-8",
    )

    attached = run_packet("attach-readiness", str(pilot_path), str(readiness_path))
    assert attached.returncode == 0, attached.stderr
    assert json.loads(attached.stdout)["readiness_level"] == "connector_ready"

    checked = run_packet("check-ready", str(pilot_path))
    assert checked.returncode != 0
    assert "pilot_candidate" in checked.stderr
