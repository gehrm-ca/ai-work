import json
from datetime import datetime, timezone

from program_os.models import ConfidenceBand, Rag
from program_os.pilot import (
    PilotBaseline,
    PilotCommercialSignal,
    PilotDisposition,
    PilotEvidenceSnapshot,
    PilotFindingReview,
    PilotFindingType,
    PilotRecord,
    new_pilot_record,
)
from program_os.readiness import EvidenceReadinessLevel


def test_new_pilot_is_not_ready_until_baseline_and_snapshot_exist():
    record = new_pilot_record("pilot-1", "Program A")
    assert record.ready_for_analysis is False


def test_pilot_ready_requires_frozen_human_baseline_and_evidence_snapshot():
    record = PilotRecord(
        pilot_id="pilot-1",
        program_alias="Program A",
        started_at=datetime.now(timezone.utc),
        baseline=PilotBaseline(
            recorded_at=datetime.now(timezone.utc),
            official_rag=Rag.GREEN,
            forecast_expectation="On track.",
            plan_confidence=ConfidenceBand.MODERATE,
        ),
        evidence_snapshot=PilotEvidenceSnapshot(
            snapshot_id="snap-1",
            captured_at=datetime.now(timezone.utc),
            source_types=("jira", "meeting_notes"),
            evidence_count=42,
            private_location="var/pilots/pilot-1/evidence",
            readiness_level=EvidenceReadinessLevel.PILOT_CANDIDATE,
        ),
    )
    assert record.ready_for_analysis is True


def test_aggregate_summary_excludes_finding_text_and_evidence_ids():
    record = PilotRecord(
        pilot_id="pilot-1",
        program_alias="Program A",
        started_at=datetime.now(timezone.utc),
        findings=[
            PilotFindingReview(
                finding_id="finding-1",
                finding_type=PilotFindingType.RISK,
                disposition=PilotDisposition.ACCEPT,
                rationale="Private rationale that must not appear in aggregate output.",
                evidence_ids=("PRIVATE-123",),
            ),
            PilotFindingReview(
                finding_id="finding-2",
                finding_type=PilotFindingType.RECOMMENDATION,
                disposition=PilotDisposition.MODIFY,
                rationale="Another private rationale.",
                evidence_ids=("PRIVATE-456",),
            ),
            PilotFindingReview(
                finding_id="finding-3",
                finding_type=PilotFindingType.CONTRADICTION,
                disposition=PilotDisposition.REJECT,
                rationale="Incorrect inference.",
            ),
        ],
        commercial_signal=PilotCommercialSignal(
            would_run_again_next_week=True,
            would_use_in_real_operating_review=True,
            willingness_to_continue_paid_pilot=True,
        ),
    )

    summary = record.aggregate_summary()
    serialized = json.dumps(summary)

    assert summary["finding_count"] == 3
    assert summary["dispositions"] == {
        "Accept": 1,
        "Modify": 1,
        "Reject": 1,
    }
    assert summary["material_accept_or_modify_count"] == 2
    assert summary["would_run_again_next_week"] is True
    assert "Private rationale" not in serialized
    assert "PRIVATE-123" not in serialized


def test_pilot_is_not_ready_with_connector_only_evidence():
    record = PilotRecord(
        pilot_id="pilot-connector-only",
        program_alias="Program A",
        started_at=datetime.now(timezone.utc),
        baseline=PilotBaseline(
            recorded_at=datetime.now(timezone.utc),
            official_rag=Rag.GREEN,
            forecast_expectation="On track.",
            plan_confidence=ConfidenceBand.MODERATE,
        ),
        evidence_snapshot=PilotEvidenceSnapshot(
            snapshot_id="snap-connector",
            captured_at=datetime.now(timezone.utc),
            source_types=("jira",),
            evidence_count=12,
            private_location="var/pilots/pilot-connector/evidence",
            readiness_level=EvidenceReadinessLevel.CONNECTOR_READY,
        ),
    )

    assert record.ready_for_analysis is False
    assert record.aggregate_summary()["evidence_readiness_level"] == "connector_ready"


def test_pilot_is_not_ready_when_readiness_has_not_been_attached():
    record = PilotRecord(
        pilot_id="pilot-no-readiness",
        program_alias="Program A",
        started_at=datetime.now(timezone.utc),
        baseline=PilotBaseline(
            recorded_at=datetime.now(timezone.utc),
            official_rag=Rag.GREEN,
            forecast_expectation="On track.",
            plan_confidence=ConfidenceBand.MODERATE,
        ),
        evidence_snapshot=PilotEvidenceSnapshot(
            snapshot_id="snap-unprofiled",
            captured_at=datetime.now(timezone.utc),
            source_types=("jira", "risk_log"),
            evidence_count=12,
            private_location="var/pilots/pilot-unprofiled/evidence",
        ),
    )

    assert record.ready_for_analysis is False
    assert record.aggregate_summary()["evidence_readiness_level"] is None
