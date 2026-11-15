"""Program OS read-only source adapters."""

from .base import (
    IngestionBatch,
    IngestionFailure,
    IngestionFailureKind,
    PermissionContext,
    ReadOnlyAdapter,
    SourceRecord,
    normalize_batch,
)
from .json_import import ReadOnlyJsonAdapter

__all__ = [
    "IngestionBatch",
    "IngestionFailure",
    "IngestionFailureKind",
    "PermissionContext",
    "ReadOnlyAdapter",
    "ReadOnlyJsonAdapter",
    "SourceRecord",
    "normalize_batch",
]
