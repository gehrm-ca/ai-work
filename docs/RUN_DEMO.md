# Running the V2 demo

## Fastest path

From the repository root:

```bash
make demo
```

The launcher creates a local Python virtual environment if needed, installs the Python package, installs frontend dependencies if needed, starts FastAPI on port 8000, starts Next.js on port 3000, writes logs under `var/`, and stops both services together on Ctrl-C.

Open http://127.0.0.1:3000.

The deterministic Atlas demo does not require an API key.

## Manual backend

```bash
python -m pip install -e ".[dev]"
uvicorn program_os.api:app --reload --port 8000
```

Deterministic demo data is available at:

- `GET /health`
- `GET /atlas/demo`

The optional live agent draft endpoint is:

- `POST /atlas/agent-draft`

It requires both `PROGRAM_OS_ENABLE_LIVE_AGENT=true` and `OPENAI_API_KEY`. The explicit feature flag prevents an API key from accidentally enabling model calls in a public deterministic deployment.

Capability state is visible at:

- `GET /capabilities`

The deterministic demo remains functional without a model key.

Human override + audit:

- `POST /atlas/override`

Audit records default to `/tmp/program-os/audit.jsonl` and do not modify model behavior.

## Manual frontend

```bash
cd web
npm install
PROGRAM_OS_API_URL=http://127.0.0.1:8000 npm run dev
```

Open http://localhost:3000.

## Demo sequence

1. Show official GREEN versus forecast AMBER.
2. Review Monday interventions sorted by portfolio priority.
3. Drill into source IDs for the partner-date contradiction and defect trend.
4. Show the resource tradeoff and its downside to AI work.
5. Show Friday status.
6. Submit an override through the API and inspect the audit + unapproved learning proposal.


## Containerized preview

```bash
docker compose up --build
```

Open http://127.0.0.1:3000.

See [Hosted deterministic demo](HOSTED_DEMO.md) for the public deployment boundary.
