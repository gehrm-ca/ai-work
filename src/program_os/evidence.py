"""Load immutable evidence observations from synthetic or connector-normalized data."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

from .models import Evidence

ATLAS_DATA_FILES = (
    "jira_issues.json",
    "risks.json",
    "project_pages.json",
    "meeting_notes.json",
    "quality_reports.json",
    "decisions.json",
    "retrospectives.json",
    "budget_snapshots.json",
    "resource_snapshots.json",
    "status_reports.json",
    "dependencies.json",
    "milestones.json",
)

_META_FIELDS = {
    "source_type",
    "source_id",
    "project_id",
    "source_updated_at",
    "retrieved_at",
    "authority_tier",
}


def record_to_evidence(record: dict) -> Evidence:
    missing = _META_FIELDS.difference(record)
    if missing:
        raise ValueError(f"Evidence record missing required fields: {sorted(missing)}")
    payload = {key: value for key, value in record.items() if key not in _META_FIELDS}
    return Evidence(
        evidence_id=record["source_id"],
        source_type=record["source_type"],
        source_id=record["source_id"],
        project_id=record["project_id"],
        source_updated_at=record["source_updated_at"],
        retrieved_at=record["retrieved_at"],
        authority_tier=record["authority_tier"],
        payload=payload,
    )


def _records(payload: object) -> Iterable[dict]:
    if isinstance(payload, list):
        for item in payload:
            if not isinstance(item, dict):
                raise ValueError("Evidence arrays may only contain JSON objects.")
            yield item
    elif isinstance(payload, dict):
        yield payload
    else:
        raise ValueError("Evidence files must contain a JSON object or array.")


def load_evidence_dir(data_dir: Path, files: Iterable[str] = ATLAS_DATA_FILES) -> list[Evidence]:
    evidence: list[Evidence] = []
    for filename in files:
        payload = json.loads((data_dir / filename).read_text(encoding="utf-8"))
        evidence.extend(record_to_evidence(record) for record in _records(payload))

    ids = [item.evidence_id for item in evidence]
    if len(ids) != len(set(ids)):
        raise ValueError("Evidence IDs must be unique within a snapshot.")
    return evidence


def index_evidence(evidence: Iterable[Evidence]) -> dict[str, Evidence]:
    return {item.evidence_id: item for item in evidence}
