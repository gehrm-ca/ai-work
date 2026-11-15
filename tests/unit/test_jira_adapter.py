import base64
import json

import httpx

from program_os.adapters import IngestionFailureKind, normalize_batch
from program_os.adapters.jira_cloud import JiraCloudAdapter


def issue(key: str, updated: str = "2026-11-15T12:00:00.000+0000") -> dict:
    return {
        "id": key.split("-")[-1],
        "key": key,
        "fields": {
            "summary": f"Summary {key}",
            "status": {"name": "In Progress"},
            "updated": updated,
            "duedate": "2026-11-20",
            "assignee": {
                "accountId": "abc123",
                "displayName": "Pilot User",
            },
            "priority": {"name": "High"},
            "issuetype": {"name": "Story"},
            "labels": ["launch"],
            "project": {"key": key.split("-")[0]},
        },
    }


def client_for(handler) -> httpx.Client:
    return httpx.Client(transport=httpx.MockTransport(handler))


def test_jira_adapter_paginates_and_preserves_permission_provenance():
    requests = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        body = json.loads(request.content)
        if "nextPageToken" not in body:
            return httpx.Response(
                200,
                json={
                    "issues": [issue("PLAT-1")],
                    "nextPageToken": "page-2",
                    "isLast": False,
                },
            )
        assert body["nextPageToken"] == "page-2"
        return httpx.Response(
            200,
            json={"issues": [issue("PLAT-2")], "isLast": True},
        )

    adapter = JiraCloudAdapter(
        base_url="https://example.atlassian.net",
        jql="project = PLAT",
        email="pilot@example.com",
        api_token="secret-token",
        client=client_for(handler),
    )
    batch = adapter.fetch()

    assert batch.complete is True
    assert [record.source_id for record in batch.records] == ["PLAT-1", "PLAT-2"]
    assert len(requests) == 2
    expected = base64.b64encode(
        b"pilot@example.com:secret-token"
    ).decode("ascii")
    assert requests[0].headers["authorization"] == f"Basic {expected}"
    assert requests[0].url.path == "/rest/api/3/search/jql"

    evidence = normalize_batch(batch)
    assert evidence[0].payload["_connector"]["permission_context"]["principal"] == (
        "pilot@example.com"
    )
    assert evidence[0].payload["_connector"]["permission_context"]["visibility"] == (
        "jira-permission-filtered"
    )
    assert evidence[0].payload["description"] if "description" in evidence[0].payload else True


def test_jira_adapter_does_not_retrieve_description_or_comments_by_default():
    seen_fields = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen_fields.extend(json.loads(request.content)["fields"])
        return httpx.Response(200, json={"issues": [issue("PLAT-1")], "isLast": True})

    batch = JiraCloudAdapter(
        base_url="https://example.atlassian.net",
        jql="project = PLAT",
        bearer_token="oauth-token",
        principal="account-123",
        client=client_for(handler),
    ).fetch()

    assert batch.complete is True
    assert "description" not in seen_fields
    assert "comment" not in seen_fields
    assert batch.records[0].permission_context.scopes == (
        "oauth-bearer",
        "read:jira-work",
    )


def test_jira_permission_denial_is_explicit():
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(403, text="forbidden")

    batch = JiraCloudAdapter(
        base_url="https://example.atlassian.net",
        jql="project = SECRET",
        bearer_token="oauth-token",
        client=client_for(handler),
    ).fetch()

    assert batch.records == ()
    assert batch.complete is False
    assert batch.failures[0].kind == IngestionFailureKind.PERMISSION
    assert "oauth-token" not in batch.failures[0].detail


def test_second_page_failure_marks_snapshot_partial_and_keeps_first_page():
    calls = 0

    def handler(request: httpx.Request) -> httpx.Response:
        nonlocal calls
        calls += 1
        if calls == 1:
            return httpx.Response(
                200,
                json={
                    "issues": [issue("PLAT-1")],
                    "nextPageToken": "page-2",
                    "isLast": False,
                },
            )
        return httpx.Response(503, text="unavailable")

    batch = JiraCloudAdapter(
        base_url="https://example.atlassian.net",
        jql="project = PLAT",
        bearer_token="oauth-token",
        client=client_for(handler),
    ).fetch()

    assert [record.source_id for record in batch.records] == ["PLAT-1"]
    kinds = [failure.kind for failure in batch.failures]
    assert IngestionFailureKind.PARTIAL_RETRIEVAL in kinds
    assert IngestionFailureKind.NETWORK in kinds
    assert batch.complete is False


def test_malformed_issue_is_reported_without_losing_valid_records():
    broken = issue("PLAT-2")
    del broken["fields"]["updated"]

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={"issues": [issue("PLAT-1"), broken], "isLast": True},
        )

    batch = JiraCloudAdapter(
        base_url="https://example.atlassian.net",
        jql="project = PLAT",
        bearer_token="oauth-token",
        client=client_for(handler),
    ).fetch()

    assert [record.source_id for record in batch.records] == ["PLAT-1"]
    kinds = [failure.kind for failure in batch.failures]
    assert IngestionFailureKind.PARTIAL_RETRIEVAL in kinds
    assert IngestionFailureKind.MALFORMED_RECORD in kinds


def test_auth_modes_are_mutually_exclusive():
    try:
        JiraCloudAdapter(
            base_url="https://example.atlassian.net",
            jql="project = PLAT",
            email="pilot@example.com",
            api_token="token",
            bearer_token="bearer",
        )
    except ValueError as exc:
        assert "either basic" in str(exc)
    else:
        raise AssertionError("Expected auth configuration error.")
