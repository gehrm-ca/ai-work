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
from .jira_cloud import JiraCloudAdapter

__all__ = [
    "IngestionBatch",
    "IngestionFailure",
    "IngestionFailureKind",
    "PermissionContext",
    "ReadOnlyAdapter",
    "ReadOnlyJsonAdapter",
    "JiraCloudAdapter",
    "SourceRecord",
    "normalize_batch",
]
