# Hosted deterministic demo

## Goal

Publish the Atlas V2 demo so reviewers can experience Program OS without cloning the repository or supplying an OpenAI API key.

The public demo is intentionally deterministic. It must never become a live model endpoint merely because a hosting environment contains an API key.

## Safety boundary

Live model calls require both:

1. `PROGRAM_OS_ENABLE_LIVE_AGENT=true`
2. a valid `OPENAI_API_KEY`

The default is:

```text
PROGRAM_OS_ENABLE_LIVE_AGENT=false
```

The public container configuration keeps this false.

The capability state can be checked at:

```text
GET /capabilities
```

Expected public-demo response:

```json
{
  "deterministic_demo": true,
  "live_agent_enabled": false
}
```

## Containerized local preview

Build and run both services:

```bash
docker compose up --build
```

Then open:

- UI: http://127.0.0.1:3000
- API health: http://127.0.0.1:8000/health
- API capabilities: http://127.0.0.1:8000/capabilities

Stop with:

```bash
docker compose down
```

## Deployment contract

A public deployment must preserve these properties:

- synthetic Atlas data only;
- `PROGRAM_OS_ENABLE_LIVE_AGENT=false`;
- no OpenAI key required;
- no customer or employer data;
- no production system-of-record credentials;
- no consequential write-back;
- audit output is ephemeral or isolated;
- API and UI are reproducible from the repository containers.

## Production live-agent deployment

A future secured live-agent deployment is a different trust boundary.

Before enabling it:

- authenticate users;
- authorize per tenant/project;
- propagate source permissions;
- store secrets in a managed secret store;
- isolate audit records by tenant;
- rate-limit model calls;
- log model/configuration versions;
- define evidence retention/deletion;
- review provider data-handling requirements.

Do not enable the live-agent flag on the public showcase deployment.
