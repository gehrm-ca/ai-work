"""Read-only source-adapter contracts for Program OS.

Adapters return both records and failures. Missing, denied, or malformed source
objects must never be silently interpreted as absence of risk.
"""
from __future__ import annotations

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Protocol

from pydantic import BaseModel, ConfigDict, Field

from program_os.models import Evidence


class IngestionFailureKind(str, Enum):
    AUTHENTICATION = "authentication"
    PERMISSION = "permission"
    MALFORMED_RECORD = "malformed_record"
    PARTIAL_RETRIEVAL = "partial_retrieval"
    NETWORK = "network"
    UNKNOWN = "unknown"


class PermissionContext(BaseModel):
    model_config = ConfigDict(frozen=True)

    principal: str | None = None
    scopes: tuple[str, ...] = ()
    visibility: str | None = None


class SourceRecord(BaseModel):
    model_config = ConfigDict(frozen=True)

    source_type: str
    source_id: str
    project_id: str
    source_updated_at: datetime
    authority_tier: int = Field(ge=1, le=5)
    payload: dict[str, Any]
    source_url: str | None = None
    permission_context: PermissionContext = Field(default_factory=PermissionContext)


class IngestionFailure(BaseModel):
    model_config = ConfigDict(frozen=True)

    kind: IngestionFailureKind
    source_ref: str | None = None
    detail: str
    retryable: bool = False


class IngestionBatch(BaseModel):
    model_config = ConfigDict(frozen=True)

    connector_id: str
    retrieved_at: datetime
    records: tuple[SourceRecord, ...] = ()
    failures: tuple[IngestionFailure, ...] = ()

    @property
    def complete(self) -> bool:
        return not self.failures


class ReadOnlyAdapter(Protocol):
    connector_id: str

    def fetch(self) -> IngestionBatch:
        """Return a point-in-time read-only snapshot plus explicit failures."""


def normalize_batch(batch: IngestionBatch) -> list[Evidence]:
    """Convert a connector batch into immutable Program OS evidence."""
    evidence: list[Evidence] = []
    seen: set[str] = set()

    for record in batch.records:
        if record.source_id in seen:
            raise ValueError(
                f"Duplicate source_id {record.source_id!r} in connector snapshot."
            )
        seen.add(record.source_id)
        payload = dict(record.payload)
        payload["_connector"] = {
            "connector_id": batch.connector_id,
            "source_url": record.source_url,
            "permission_context": record.permission_context.model_dump(mode="json"),
        }
        evidence.append(
            Evidence(
                evidence_id=record.source_id,
                source_type=record.source_type,
                source_id=record.source_id,
                project_id=record.project_id,
                source_updated_at=record.source_updated_at,
                retrieved_at=batch.retrieved_at,
                authority_tier=record.authority_tier,
                payload=payload,
            )
        )
    return evidence


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
