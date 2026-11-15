"""Read-only JSON adapter for sandbox, export, and contract testing.

This adapter is intentionally simple: it proves the source contract before
production OAuth or vendor SDK complexity is introduced.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from pydantic import ValidationError

from .base import (
    IngestionBatch,
    IngestionFailure,
    IngestionFailureKind,
    PermissionContext,
    SourceRecord,
    now_utc,
)


class ReadOnlyJsonAdapter:
    def __init__(
        self,
        path: Path,
        *,
        connector_id: str,
        principal: str | None = None,
        scopes: tuple[str, ...] = ("read",),
    ) -> None:
        self.path = path
        self.connector_id = connector_id
        self.permission_context = PermissionContext(
            principal=principal,
            scopes=scopes,
            visibility="export",
        )

    def fetch(self) -> IngestionBatch:
        retrieved_at = now_utc()
        if not self.path.exists():
            return IngestionBatch(
                connector_id=self.connector_id,
                retrieved_at=retrieved_at,
                failures=(
                    IngestionFailure(
                        kind=IngestionFailureKind.PERMISSION,
                        source_ref=str(self.path),
                        detail="Source export is unavailable or inaccessible.",
                        retryable=False,
                    ),
                ),
            )

        try:
            raw: Any = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            return IngestionBatch(
                connector_id=self.connector_id,
                retrieved_at=retrieved_at,
                failures=(
                    IngestionFailure(
                        kind=IngestionFailureKind.MALFORMED_RECORD,
                        source_ref=str(self.path),
                        detail=f"Could not parse source export: {exc}",
                        retryable=False,
                    ),
                ),
            )

        rows = raw if isinstance(raw, list) else [raw]
        records: list[SourceRecord] = []
        failures: list[IngestionFailure] = []

        for index, row in enumerate(rows):
            if not isinstance(row, dict):
                failures.append(
                    IngestionFailure(
                        kind=IngestionFailureKind.MALFORMED_RECORD,
                        source_ref=f"{self.path}#{index}",
                        detail="Source record must be a JSON object.",
                    )
                )
                continue

            candidate = dict(row)
            candidate.setdefault("permission_context", self.permission_context)
            try:
                records.append(SourceRecord.model_validate(candidate))
            except ValidationError as exc:
                failures.append(
                    IngestionFailure(
                        kind=IngestionFailureKind.MALFORMED_RECORD,
                        source_ref=str(row.get("source_id") or f"{self.path}#{index}"),
                        detail=exc.errors(include_url=False).__repr__(),
                    )
                )

        if records and failures:
            failures.insert(
                0,
                IngestionFailure(
                    kind=IngestionFailureKind.PARTIAL_RETRIEVAL,
                    source_ref=str(self.path),
                    detail=(
                        f"Loaded {len(records)} record(s) but "
                        f"{len(failures)} record-level failure(s) occurred."
                    ),
                    retryable=False,
                ),
            )

        return IngestionBatch(
            connector_id=self.connector_id,
            retrieved_at=retrieved_at,
            records=tuple(records),
            failures=tuple(failures),
        )
