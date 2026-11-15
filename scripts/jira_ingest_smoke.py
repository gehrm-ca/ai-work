"""Manual Jira Cloud read-only connector smoke test.

Credentials are read from environment variables and are never printed.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

from program_os.adapters import normalize_batch
from program_os.adapters.jira_cloud import JiraCloudAdapter


def required(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise SystemExit(f"{name} is required.")
    return value


def main() -> None:
    base_url = required("JIRA_BASE_URL")
    jql = os.getenv("JIRA_JQL", "order by updated DESC")
    bearer = os.getenv("JIRA_BEARER_TOKEN")
    email = os.getenv("JIRA_EMAIL")
    api_token = os.getenv("JIRA_API_TOKEN")

    kwargs = {
        "base_url": base_url,
        "jql": jql,
        "principal": os.getenv("JIRA_PRINCIPAL") or email,
    }
    if bearer:
        kwargs["bearer_token"] = bearer
    else:
        if not email or not api_token:
            raise SystemExit(
                "Set JIRA_BEARER_TOKEN or both JIRA_EMAIL and JIRA_API_TOKEN."
            )
        kwargs["email"] = email
        kwargs["api_token"] = api_token

    with JiraCloudAdapter(**kwargs) as adapter:
        batch = adapter.fetch()

    evidence = normalize_batch(batch)
    summary = {
        "connector_id": batch.connector_id,
        "records": len(evidence),
        "complete": batch.complete,
        "failure_kinds": [failure.kind.value for failure in batch.failures],
        "sample_evidence_ids": [item.evidence_id for item in evidence[:10]],
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
