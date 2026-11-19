# Running the V2 demo

## Fastest path

You need Python 3.12 or newer, Node.js 20.9 or newer, and macOS or Linux. On Windows, use the [containerized preview](#containerized-preview).

From the repository root:

~~~bash
make demo
~~~

The launcher creates a local Python virtual environment if needed, installs the pinned direct Python dependencies, installs frontend dependencies if needed, starts FastAPI on port 8000, starts Next.js on port 3000, writes logs under var/, and stops both services together on Ctrl-C.

Open http://127.0.0.1:3000.

The deterministic Atlas demo does not require an API key. Optional protected UI operations now require a **separate local UI access token** and login.

## Manual backend

~~~bash
python -m pip install -e ".[dev]"
uvicorn program_os.api:app --reload --port 8000
~~~

Deterministic demo data is available at:

- GET /health
- GET /atlas/demo
- GET /atlas/evidence/{evidence_id}
- GET /capabilities

These read-only endpoints do not require authentication in the local demo.

## Protected operations

Human override and live-agent draft endpoints are disabled unless PROGRAM_OS_API_TOKEN is configured.

Generate a local token:

~~~bash
export PROGRAM_OS_API_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
export PROGRAM_OS_UI_TOKEN="$(python -c 'import secrets; print(secrets.token_urlsafe(32))')"
~~~

Protected requests must send:

~~~text
Authorization: Bearer <PROGRAM_OS_API_TOKEN>
~~~

The optional live agent draft endpoint is:

- POST /atlas/agent-draft

It additionally requires both PROGRAM_OS_ENABLE_LIVE_AGENT=true and OPENAI_API_KEY. The explicit feature flag, model key and API bearer token are independent gates; possessing a model key alone never enables public model calls.

Capability state is visible at GET /capabilities. A deterministic deployment should report live_agent_enabled as false.

Human override + audit:

- POST /atlas/override

When both `PROGRAM_OS_API_TOKEN` and `PROGRAM_OS_UI_TOKEN` are set, start the local demo and visit http://127.0.0.1:3000/login. Enter **only** the separate `PROGRAM_OS_UI_TOKEN`, not the backend API token. The UI issues an eight-hour HttpOnly session cookie, and the **Human accountability** panel then becomes available. The browser never receives the backend bearer token. The proxy assigns the actor `local-authenticated-operator`; this is a shared local operator identity and not enterprise identity proof.

The public GitHub Pages showcase remains static and read-only.

The protected API can still be exercised directly:

~~~bash
curl -s -X POST http://127.0.0.1:8000/atlas/override \
  -H "authorization: Bearer $PROGRAM_OS_API_TOKEN" \
  -H 'content-type: application/json' \
  -d '{"actor": "you", "assessment_id": "atlas-portfolio", "new_status": "RED", "rationale": "Partner date is unconfirmed."}'
~~~

The response contains the override, the audit event and an unapproved learning proposal.

Audit records are stored at `var/audit.jsonl` under `make demo`. The Docker path stores them in the named volume `program_os_audit` at `/var/program-os/audit.jsonl`, so container recreation does not silently erase the local decision history. These prototype audit records do not modify model behavior and are not production tamper-evident storage.

Protected operations have an in-process demo rate limit controlled by PROGRAM_OS_PROTECTED_RPM (default 30 requests per minute per client). Live-agent calls have an additional per-process quota (`PROGRAM_OS_MAX_LIVE_CALLS_PER_PROCESS`, default 10), not a guaranteed dollar ceiling. Configure a provider-enforced spend limit separately. Audit integrity can be checked with `AuditStore(Path("var/audit.jsonl")).verify_integrity()` from Python; local file owners can still rewrite history. These controls do not replace enterprise identity, tenancy or production gateway controls.

## Manual frontend

~~~bash
cd web
npm install
PROGRAM_OS_API_URL=http://127.0.0.1:8000 npm run dev
~~~

Open http://localhost:3000.

## Demo sequence

1. Compare official GREEN with forecast AMBER.
2. Review Monday interventions sorted by portfolio priority.
3. Open the source IDs for the partner-date contradiction and defect trend; inspect source freshness, authority tier and the immutable observed payload.
4. Expand **Why this conclusion · what would change it** on a finding and verify the reasoning factor and clearing condition are concrete.
5. Review the resource tradeoff and its downside to AI work.
6. Read the Friday status.
7. Optionally configure both `PROGRAM_OS_API_TOKEN` and `PROGRAM_OS_UI_TOKEN`, log in at `/login`, record a human status decision in the local UI, and inspect the override ID, audit event, and unapproved learning proposal.
8. Compare the behavior with the measured evaluation results.

## Containerized preview

~~~bash
docker compose up --build
~~~

Open http://127.0.0.1:3000.

The Compose ports bind to 127.0.0.1 by default. This configuration is intentionally **local-demo-only** and should not be changed to a public bind address without implementing the production controls described in [Production trust boundaries](PRODUCTION_TRUST_BOUNDARIES.md).

To exercise protected operations through Compose, set **both** `PROGRAM_OS_API_TOKEN` and `PROGRAM_OS_UI_TOKEN` in the shell before starting the containers. Compose passes the API token to both services and the UI token only to Next.js. Visit `/login` and enter the UI token. Neither backend token is included in frontend assets. The containers now run as non-root; previously created audit volumes may require a one-time ownership migration, preserving any existing audit history.

Inspect Docker audit records with:

~~~bash
docker compose exec api cat /var/program-os/audit.jsonl
~~~

Delete containers and the retained audit volume after testing with sensitive rationale:

~~~bash
docker compose down -v
~~~

See [Hosted deterministic demo](HOSTED_DEMO.md) for the public deployment boundary and [Use Program OS on your own](USE_YOUR_OWN_PROGRAM.md) for pilot ingestion.
