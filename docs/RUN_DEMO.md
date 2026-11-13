# Running the V2 demo

## Backend

```bash
python -m pip install -e ".[dev]"
uvicorn program_os.api:app --reload --port 8000
```

Deterministic demo data is available at:

- `GET /health`
- `GET /atlas/demo`

The optional live agent draft endpoint is:

- `POST /atlas/agent-draft`

It requires `OPENAI_API_KEY`. The deterministic demo remains functional without a model key.

Human override + audit:

- `POST /atlas/override`

Audit records default to `/tmp/program-os/audit.jsonl` and do not modify model behavior.

## Frontend

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
