from datetime import datetime, timedelta, timezone

from program_os.adapters import (
    IngestionBatch,
    IngestionFailure,
    IngestionFailureKind,
    PermissionContext,
    SourceRecord,
)
from program_os.readiness import EvidenceReadinessLevel, assess_evidence_readiness


NOW = datetime(2026, 11, 16, 20, 0, tzinfo=timezone.utc)


def record(
    source_id: str,
    *,
    source_type: str,
    project_id: str,
    age_hours: int = 12,
    authority_tier: int = 1,
    permission: bool = True,
    source_url: bool = True,
) -> SourceRecord:
    return SourceRecord(
        source_type=source_type,
        source_id=source_id,
        project_id=project_id,
        source_updated_at=NOW - timedelta(hours=age_hours),
        authority_tier=authority_tier,
        payload={"summary": "Private content must not appear in readiness output."},
        source_url=(
            f"https://example.invalid/{source_id}" if source_url else None
        ),
        permission_context=(
            PermissionContext(
                principal="pilot-user",
                scopes=("read",),
                visibility="source-filtered",
            )
            if permission
            else PermissionContext()
        ),
    )


def test_cross_source_portfolio_snapshot_is_pilot_candidate():
    batch = IngestionBatch(
        connector_id="pilot-bundle",
        retrieved_at=NOW,
        records=(
            record("JIRA-1", source_type="jira", project_id="A"),
            record("JIRA-2", source_type="jira", project_id="B"),
            record("RISK-1", source_type="risk_log", project_id="A", authority_tier=2),
            record("STATUS-1", source_type="exec_status", project_id="B", authority_tier=3),
        ),
    )

    report = assess_evidence_readiness(batch)

    assert report.readiness_level == EvidenceReadinessLevel.PILOT_CANDIDATE
    assert report.suitable_for_pilot_analysis is True
    assert report.cross_source_evidence_available is True
    assert report.portfolio_evidence_available is True
    assert report.high_authority_evidence_available is True
    assert report.permission_context_coverage_pct == 100.0
    assert report.source_url_coverage_pct == 100.0


def test_single_source_snapshot_is_connector_ready_not_full_pilot_candidate():
    batch = IngestionBatch(
        connector_id="jira-cloud",
        retrieved_at=NOW,
        records=(
            record("JIRA-1", source_type="jira", project_id="A"),
            record("JIRA-2", source_type="jira", project_id="B"),
        ),
    )

    report = assess_evidence_readiness(batch)

    assert report.readiness_level == EvidenceReadinessLevel.CONNECTOR_READY
    assert report.suitable_for_pilot_analysis is False
    assert report.cross_source_evidence_available is False
    assert any("Only one source type" in item for item in report.limitations)


def test_incomplete_snapshot_is_blocked_even_with_multiple_sources():
    batch = IngestionBatch(
        connector_id="pilot-bundle",
        retrieved_at=NOW,
        records=(
            record("JIRA-1", source_type="jira", project_id="A"),
            record("RISK-1", source_type="risk_log", project_id="B"),
        ),
        failures=(
            IngestionFailure(
                kind=IngestionFailureKind.PARTIAL_RETRIEVAL,
                detail="Page limit reached.",
            ),
        ),
    )

    report = assess_evidence_readiness(batch)

    assert report.readiness_level == EvidenceReadinessLevel.BLOCKED
    assert report.ingestion_complete is False
    assert report.failure_kinds == ("partial_retrieval",)


def test_readiness_report_flags_staleness_and_permission_gaps():
    batch = IngestionBatch(
        connector_id="pilot-bundle",
        retrieved_at=NOW,
        records=(
            record(
                "JIRA-1",
                source_type="jira",
                project_id="A",
                age_hours=240,
                permission=False,
                source_url=False,
            ),
            record("RISK-1", source_type="risk_log", project_id="B"),
        ),
    )

    report = assess_evidence_readiness(batch, stale_after_days=7)

    assert report.stale_record_count == 1
    assert report.stale_record_pct == 50.0
    assert report.permission_context_coverage_pct == 50.0
    assert report.source_url_coverage_pct == 50.0
    assert any("freshness" in item for item in report.limitations)
    assert any("Permission context" in item for item in report.limitations)


def test_readiness_report_does_not_expose_source_or_project_identifiers():
    batch = IngestionBatch(
        connector_id="pilot-bundle",
        retrieved_at=NOW,
        records=(
            record("SECRET-ISSUE-123", source_type="jira", project_id="SECRET-A"),
            record("SECRET-RISK-456", source_type="risk_log", project_id="SECRET-B"),
        ),
    )

    serialized = assess_evidence_readiness(batch).model_dump_json()

    assert "SECRET-ISSUE-123" not in serialized
    assert "SECRET-RISK-456" not in serialized
    assert "SECRET-A" not in serialized
    assert "SECRET-B" not in serialized
    assert "Private content" not in serialized
