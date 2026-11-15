# Jira Cloud read-only connector

**Status:** V2.1 pilot connector.  
**Issue:** [#17](https://github.com/gehrm-ca/ai-work/issues/17)

## Purpose

This adapter proves that Program OS can ingest a real Jira Cloud issue stream while preserving source identity, freshness, and permission context.

It is read-only.

## API contract

The adapter uses Jira Cloud REST API v3 enhanced JQL search:

```text
POST /rest/api/3/search/jql
```

It follows `nextPageToken` pagination.

Jira search results remain subject to the authenticated principal's Jira permissions, including Browse Projects and issue-level security where applicable. Program OS preserves the connector permission context and must not broaden access after ingestion.

Official references:

- https://developer.atlassian.com/cloud/jira/platform/rest/v3/api-group-issue-search/
- https://developer.atlassian.com/cloud/jira/platform/basic-auth-for-rest-apis/
- https://developer.atlassian.com/cloud/jira/platform/security-overview/

## Data minimization

Default fields:

- summary
- status
- updated timestamp
- due date
- assignee
- priority
- issue type
- labels
- project

The pilot adapter deliberately does **not** retrieve issue description or comments by default. Those fields increase privacy and prompt-injection exposure and should only be added if evaluation evidence shows they are necessary.

## Authentication

### Pilot / script path

Jira Cloud supports Basic authentication using an Atlassian account email plus API token for scripts and REST clients.

Environment:

```bash
export JIRA_BASE_URL=https://your-site.atlassian.net
export JIRA_EMAIL=you@example.com
export JIRA_API_TOKEN=...
export JIRA_JQL='project = YOURKEY order by updated DESC'
python scripts/jira_ingest_smoke.py
```

Do not use an Atlassian password.

Do not commit the token.

### OAuth-oriented path

The adapter also accepts a bearer access token:

```bash
export JIRA_BASE_URL=https://your-site.atlassian.net
export JIRA_BEARER_TOKEN=...
export JIRA_PRINCIPAL=account-or-user-reference
export JIRA_JQL='project = YOURKEY order by updated DESC'
python scripts/jira_ingest_smoke.py
```

For OAuth 2.0 (3LO), Atlassian API calls use the gateway form
`https://api.atlassian.com/ex/jira/{cloudId}`, not the human site URL. Obtain
the authorized `cloudId` from `GET https://api.atlassian.com/oauth/token/accessible-resources`.
`JIRA_BROWSE_BASE_URL` is optional metadata used only to preserve human-readable
issue links such as `https://your-site.atlassian.net/browse/KEY-123`.

For a distributed/production integration, OAuth 2.0 authorization is preferred over long-lived user API tokens.

## Failure semantics

The adapter does not silently treat an incomplete fetch as complete evidence.

It distinguishes:

- authentication failure;
- permission denial;
- network/rate-limit/server failure;
- malformed record;
- partial retrieval.

If page one succeeds and page two fails, page-one evidence is retained but the snapshot is explicitly marked partial. Downstream confidence must treat incomplete coverage accordingly.

## Pilot acceptance still outstanding

The implementation and contract tests are not enough to close #17.

The issue closes only after a real or vendor-sandbox Jira site is fetched and Program OS demonstrates:

- preserved provenance;
- visible permission/coverage state;
- imported evidence in an assessment;
- no write permission;
- safe behavior under partial/inaccessible data.
