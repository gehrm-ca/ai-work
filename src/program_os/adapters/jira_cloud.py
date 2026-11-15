"""Read-only Jira Cloud adapter using the v3 enhanced JQL search API.

The adapter deliberately retrieves a small field set and preserves Jira's
permission filtering. Basic API-token auth is supported for pilot/script use;
OAuth bearer tokens are supported for production-oriented integration paths.
"""
from __future__ import annotations

import base64
from typing import Any

import httpx

from .base import (
    IngestionBatch,
    IngestionFailure,
    IngestionFailureKind,
    PermissionContext,
    SourceRecord,
    now_utc,
)


_DEFAULT_FIELDS = (
    "summary",
    "status",
    "updated",
    "duedate",
    "assignee",
    "priority",
    "issuetype",
    "labels",
    "project",
)


class JiraCloudAdapter:
    def __init__(
        self,
        *,
        base_url: str,
        jql: str,
        browse_base_url: str | None = None,
        connector_id: str = "jira-cloud",
        email: str | None = None,
        api_token: str | None = None,
        bearer_token: str | None = None,
        principal: str | None = None,
        authority_tier: int = 1,
        page_size: int = 100,
        max_pages: int = 100,
        fields: tuple[str, ...] = _DEFAULT_FIELDS,
        client: httpx.Client | None = None,
    ) -> None:
        basic = email is not None or api_token is not None
        bearer = bearer_token is not None
        if basic and bearer:
            raise ValueError("Configure either basic API-token auth or bearer auth, not both.")
        if basic and (email is None or api_token is None):
            raise ValueError("Basic Jira auth requires both email and api_token.")
        if not basic and not bearer:
            raise ValueError("Jira authentication is required.")
        if not 1 <= authority_tier <= 5:
            raise ValueError("authority_tier must be between 1 and 5.")
        if page_size < 1:
            raise ValueError("page_size must be positive.")
        if max_pages < 1:
            raise ValueError("max_pages must be positive.")

        self.base_url = base_url.rstrip("/")
        self.browse_base_url = browse_base_url.rstrip("/") if browse_base_url else None
        self.jql = jql
        self.connector_id = connector_id
        self.email = email
        self._api_token = api_token
        self._bearer_token = bearer_token
        self.principal = principal or email
        self.authority_tier = authority_tier
        self.page_size = page_size
        self.max_pages = max_pages
        self.fields = fields
        self._client = client or httpx.Client(timeout=30.0)
        self._owns_client = client is None

    def close(self) -> None:
        if self._owns_client:
            self._client.close()

    def __enter__(self) -> "JiraCloudAdapter":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.close()

    def _headers(self) -> dict[str, str]:
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        if self._bearer_token is not None:
            headers["Authorization"] = f"Bearer {self._bearer_token}"
        else:
            raw = f"{self.email}:{self._api_token}".encode("utf-8")
            token = base64.b64encode(raw).decode("ascii")
            headers["Authorization"] = f"Basic {token}"
        return headers

    def _permission_context(self) -> PermissionContext:
        scopes = (
            ("oauth-bearer", "read:jira-work")
            if self._bearer_token is not None
            else ("source-user-permissions",)
        )
        return PermissionContext(
            principal=self.principal,
            scopes=scopes,
            visibility="jira-permission-filtered",
        )

    def _issue_to_record(self, issue: dict[str, Any]) -> SourceRecord:
        key = issue.get("key")
        fields = issue.get("fields")
        if not isinstance(key, str) or not key:
            raise ValueError("Jira issue is missing key.")
        if not isinstance(fields, dict):
            raise ValueError(f"Jira issue {key} is missing fields.")

        project = fields.get("project") or {}
        project_key = project.get("key")
        updated = fields.get("updated")
        if not isinstance(project_key, str) or not project_key:
            raise ValueError(f"Jira issue {key} is missing project key.")
        if not isinstance(updated, str) or not updated:
            raise ValueError(f"Jira issue {key} is missing updated timestamp.")

        status = fields.get("status") or {}
        assignee = fields.get("assignee") or {}
        priority = fields.get("priority") or {}
        issue_type = fields.get("issuetype") or {}

        payload = {
            "jira_id": issue.get("id"),
            "summary": fields.get("summary"),
            "status": status.get("name"),
            "due_date": fields.get("duedate"),
            "assignee": {
                "account_id": assignee.get("accountId"),
                "display_name": assignee.get("displayName"),
            }
            if assignee
            else None,
            "priority": priority.get("name"),
            "issue_type": issue_type.get("name"),
            "labels": fields.get("labels") or [],
        }

        return SourceRecord(
            source_type="jira",
            source_id=key,
            project_id=project_key,
            source_updated_at=updated,
            authority_tier=self.authority_tier,
            payload=payload,
            source_url=(
                f"{self.browse_base_url}/browse/{key}"
                if self.browse_base_url
                else (
                    f"{self.base_url}/browse/{key}"
                    if ".atlassian.net" in self.base_url
                    else None
                )
            ),
            permission_context=self._permission_context(),
        )

    @staticmethod
    def _failure_for_status(status: int) -> IngestionFailure:
        if status == 401:
            return IngestionFailure(
                kind=IngestionFailureKind.AUTHENTICATION,
                detail="Jira authentication failed.",
                retryable=False,
            )
        if status == 403:
            return IngestionFailure(
                kind=IngestionFailureKind.PERMISSION,
                detail="Jira denied access for the authenticated principal.",
                retryable=False,
            )
        if status == 429 or status >= 500:
            return IngestionFailure(
                kind=IngestionFailureKind.NETWORK,
                detail=f"Jira request failed with HTTP {status}.",
                retryable=True,
            )
        return IngestionFailure(
            kind=IngestionFailureKind.UNKNOWN,
            detail=f"Jira request failed with HTTP {status}.",
            retryable=False,
        )

    @staticmethod
    def _with_partial_failure(
        failures: list[IngestionFailure],
        record_count: int,
    ) -> list[IngestionFailure]:
        if record_count and failures and not any(
            failure.kind == IngestionFailureKind.PARTIAL_RETRIEVAL
            for failure in failures
        ):
            failures.insert(
                0,
                IngestionFailure(
                    kind=IngestionFailureKind.PARTIAL_RETRIEVAL,
                    detail=(
                        f"Jira returned {record_count} record(s), but the "
                        "snapshot is incomplete."
                    ),
                    retryable=any(failure.retryable for failure in failures),
                ),
            )
        return failures

    def fetch(self) -> IngestionBatch:
        retrieved_at = now_utc()
        records: list[SourceRecord] = []
        failures: list[IngestionFailure] = []
        next_page_token: str | None = None

        for _page in range(self.max_pages):
            body: dict[str, Any] = {
                "jql": self.jql,
                "maxResults": self.page_size,
                "fields": list(self.fields),
            }
            if next_page_token:
                body["nextPageToken"] = next_page_token

            try:
                response = self._client.post(
                    f"{self.base_url}/rest/api/3/search/jql",
                    headers=self._headers(),
                    json=body,
                )
            except httpx.HTTPError:
                failures.append(
                    IngestionFailure(
                        kind=IngestionFailureKind.NETWORK,
                        detail="Jira request failed before a response was received.",
                        retryable=True,
                    )
                )
                break

            if response.status_code >= 400:
                failures.append(
                    self._failure_for_status(response.status_code)
                )
                break

            try:
                payload = response.json()
            except ValueError:
                failures.append(
                    IngestionFailure(
                        kind=IngestionFailureKind.MALFORMED_RECORD,
                        detail="Jira returned a non-JSON search response.",
                    )
                )
                break

            issues = payload.get("issues")
            if not isinstance(issues, list):
                failures.append(
                    IngestionFailure(
                        kind=IngestionFailureKind.MALFORMED_RECORD,
                        detail="Jira search response is missing an issues array.",
                    )
                )
                break

            for issue in issues:
                if not isinstance(issue, dict):
                    failures.append(
                        IngestionFailure(
                            kind=IngestionFailureKind.MALFORMED_RECORD,
                            detail="Jira search returned a non-object issue.",
                        )
                    )
                    continue
                try:
                    records.append(self._issue_to_record(issue))
                except (TypeError, ValueError) as exc:
                    key = issue.get("key")
                    failures.append(
                        IngestionFailure(
                            kind=IngestionFailureKind.MALFORMED_RECORD,
                            source_ref=str(key) if key else None,
                            detail=str(exc),
                        )
                    )

            next_page_token = payload.get("nextPageToken")
            if payload.get("isLast") is True or not next_page_token:
                break
        else:
            failures.append(
                IngestionFailure(
                    kind=IngestionFailureKind.PARTIAL_RETRIEVAL,
                    detail=(
                        f"Jira pagination exceeded the configured maximum "
                        f"of {self.max_pages} pages."
                    ),
                    retryable=False,
                )
            )

        failures = self._with_partial_failure(failures, len(records))
        return IngestionBatch(
            connector_id=self.connector_id,
            retrieved_at=retrieved_at,
            records=tuple(records),
            failures=tuple(failures),
        )
