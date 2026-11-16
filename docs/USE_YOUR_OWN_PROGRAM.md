# Use Program OS on your own

Program OS has three distinct usage modes. They have different trust boundaries.

| Mode | Data | What works today | Intended use |
|---|---|---|---|
| Hosted Atlas demo | Synthetic Atlas data | Full deterministic showcase | Review the product with zero setup |
| Local Atlas demo | Synthetic Atlas data | Full V2 API + UI, optional protected operations | Reproduce and inspect the prototype |
| Pilot ingestion | Your local JSON export or read-only Jira | Source ingestion, provenance, permissions and completeness checks | Validate the connector contract before a design-partner pilot |

The current V2 analysis and dashboard are intentionally tuned to the synthetic Atlas vertical slice. **Arbitrary customer or employer data does not yet flow through the complete Monday → Friday experience without integration work.** Do not interpret the connector smoke tests as a production deployment.

## 1. Review the product without installing anything

Open the deterministic hosted demo:

https://gehrm-ca.github.io/ai-work/

It contains synthetic data only. No API key or account is required.

Use this sequence:

1. Compare official RAG with forecast RAG.
2. Read the Monday intervention queue from the top down.
3. Inspect the evidence IDs and contradictions behind the top finding.
4. Review the portfolio tradeoff and its downstream cost.
5. Read the Thursday/Friday status.
6. Compare the behavior with the measured evaluation results.

## 2. Run the full Atlas prototype locally

Prerequisites:

- Python 3.12+
- Node.js 20.9+
- macOS or Linux

~~~bash
git clone https://github.com/gehrm-ca/ai-work.git
cd ai-work
make demo
~~~

Open http://127.0.0.1:3000.

On Windows, or without local Python/Node tooling:

~~~bash
docker compose up --build
~~~

The Compose configuration binds ports to loopback only. It is a **local demo**, not a public deployment configuration.

The deterministic Atlas path does not require an OpenAI API key.

## 3. Validate a local JSON export

Program OS includes a read-only JSON adapter for sandbox/export testing. Keep the source file outside the repository so it cannot be committed accidentally.

A source record has this contract:

~~~json
{
  "source_type": "jira",
  "source_id": "DEMO-101",
  "project_id": "DEMO",
  "source_updated_at": "2026-11-16T18:00:00Z",
  "authority_tier": 2,
  "payload": {
    "summary": "Partner integration validation is incomplete",
    "status": "In Progress"
  },
  "source_url": "https://example.invalid/browse/DEMO-101"
}
~~~

Required fields are **source_type**, **source_id** (unique within a snapshot), **project_id**, **source_updated_at** (ISO-8601), **authority_tier** (1 = highest authority, 5 = lowest), and **payload**.

Optional fields include **source_url** and permission metadata.

Run the safe smoke check:

~~~bash
python -m pip install -r requirements.lock
python -m pip install --no-deps -e .
python scripts/json_ingest_smoke.py /absolute/path/to/export.json
~~~

The command prints only connector status, record count and failure categories by default. It does not print source content or IDs unless you explicitly pass **--show-source-ids**.

A successful smoke check proves that the export satisfies the read-only ingestion contract. It does **not** prove that the current Atlas-specific signal detectors understand your organization’s fields or semantics.

A sanitized example is committed at [examples/pilot/source-record-example.json](../examples/pilot/source-record-example.json).

## 4. Validate read-only Jira Cloud access

See [Jira Cloud read-only connector](JIRA_CONNECTOR.md).

The shortest pilot path is:

~~~bash
export JIRA_BASE_URL=https://your-site.atlassian.net
export JIRA_EMAIL=you@example.com
export JIRA_API_TOKEN=...
export JIRA_JQL='project = YOURKEY order by updated DESC'

python scripts/jira_ingest_smoke.py
~~~

The adapter deliberately retrieves a small field set and does not request issue descriptions or comments by default. Jira permission failures and partial retrieval are surfaced explicitly rather than silently treated as complete evidence.

Use OAuth rather than long-lived user API tokens for a distributed integration.

## 5. Protected local API operations

The read-only deterministic endpoints remain public to localhost. Override and live-agent operations require bearer authentication.

Generate a local token without committing it:

~~~bash
export PROGRAM_OS_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
~~~

Then start the demo from the same shell.

Protected requests use the HTTP header:

~~~text
Authorization: Bearer <PROGRAM_OS_API_TOKEN>
~~~

Live agent calls additionally require both:

~~~bash
export PROGRAM_OS_ENABLE_LIVE_AGENT=true
export OPENAI_API_KEY=...
~~~

An OpenAI key by itself never enables live model calls.

Protected endpoints have a small in-process demo rate limit controlled by **PROGRAM_OS_PROTECTED_RPM** (default 30/minute). A production deployment still requires gateway-level authentication, authorization and rate limiting.

## 6. Data-handling rules for pilots

Do not:

- upload employer/customer data to the public GitHub Pages demo;
- commit source exports, API tokens, audit logs or model traces;
- expose the local FastAPI port to the public internet;
- treat a successful connector smoke test as authorization to broaden source access;
- enable consequential write-back.

For a design-partner exercise, use the [pilot protocol](DESIGN_PARTNER_PILOT.md) and the [production trust boundaries](PRODUCTION_TRUST_BOUNDARIES.md).

After a local test, remove temporary exports and local audit output according to your organization’s retention requirements. The repository ignores .env files, var/ and artifacts/, but files stored elsewhere remain your responsibility.

## What is required before true self-serve production use

The current production blockers remain:

- authenticated user identity and enterprise SSO;
- tenant isolation and row-level authorization;
- source ACL propagation;
- managed secret storage and rotation;
- durable append-only audit storage;
- customer retention/deletion controls;
- production model-provider governance;
- gateway-level abuse controls;
- generic source-to-canonical mapping and organization-specific evaluation.

Those are product/security boundaries, not installation steps.
