import json
from datetime import datetime, timezone

import pytest

from program_os.adapters import (
    IngestionFailureKind,
    ReadOnlyJsonAdapter,
    normalize_batch,
)


def record(source_id: str = "JIRA-1") -> dict:
    return {
        "source_type": "jira",
        "source_id": source_id,
        "project_id": "PLAT",
        "source_updated_at": "2026-11-14T18:00:00Z",
        "authority_tier": 1,
        "payload": {
            "summary": "Partner integration",
            "status": "Blocked",
        },
        "source_url": f"https://example.invalid/browse/{source_id}",
    }


def test_read_only_adapter_preserves_provenance_and_permission_context(tmp_path):
    path = tmp_path / "jira.json"
    path.write_text(json.dumps([record()]), encoding="utf-8")

    batch = ReadOnlyJsonAdapter(
        path,
        connector_id="jira-sandbox",
        principal="pilot-user",
        scopes=("read:jira-work",),
    ).fetch()

    assert batch.complete is True
    assert len(batch.records) == 1

    evidence = normalize_batch(batch)
    assert len(evidence) == 1
    item = evidence[0]
    assert item.evidence_id == "JIRA-1"
    assert item.source_updated_at == datetime(
        2026, 11, 14, 18, 0, tzinfo=timezone.utc
    )
    assert item.retrieved_at == batch.retrieved_at
    assert item.payload["_connector"]["connector_id"] == "jira-sandbox"
    assert item.payload["_connector"]["permission_context"]["principal"] == "pilot-user"
    assert item.payload["_connector"]["permission_context"]["scopes"] == [
        "read:jira-work"
    ]


def test_partial_malformed_export_is_explicit_not_silent(tmp_path):
    path = tmp_path / "jira.json"
    path.write_text(
        json.dumps([record(), {"source_type": "jira", "source_id": "BROKEN"}]),
        encoding="utf-8",
    )

    batch = ReadOnlyJsonAdapter(path, connector_id="jira-sandbox").fetch()

    assert len(batch.records) == 1
    assert batch.complete is False
    kinds = [failure.kind for failure in batch.failures]
    assert IngestionFailureKind.PARTIAL_RETRIEVAL in kinds
    assert IngestionFailureKind.MALFORMED_RECORD in kinds


def test_inaccessible_export_returns_permission_failure(tmp_path):
    batch = ReadOnlyJsonAdapter(
        tmp_path / "missing.json",
        connector_id="jira-sandbox",
    ).fetch()

    assert batch.records == ()
    assert batch.complete is False
    assert batch.failures[0].kind == IngestionFailureKind.PERMISSION


def test_duplicate_source_ids_are_rejected_during_normalization(tmp_path):
    path = tmp_path / "jira.json"
    path.write_text(json.dumps([record(), record()]), encoding="utf-8")
    batch = ReadOnlyJsonAdapter(path, connector_id="jira-sandbox").fetch()

    with pytest.raises(ValueError, match="Duplicate source_id"):
        normalize_batch(batch)


def test_adapter_has_no_write_surface(tmp_path):
    adapter = ReadOnlyJsonAdapter(
        tmp_path / "jira.json",
        connector_id="jira-sandbox",
    )
    assert hasattr(adapter, "fetch")
    assert not hasattr(adapter, "write")
    assert not hasattr(adapter, "update")
    assert not hasattr(adapter, "delete")
