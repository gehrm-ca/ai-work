# Hosted deterministic demo

## Goal

Publish the Atlas V2 demo so reviewers can experience Program OS without cloning the repository or supplying an OpenAI API key.

The public demo is intentionally deterministic. It must never become a live model endpoint merely because a hosting environment contains an API key.

## Safety boundary

The GitHub Pages showcase is static. It contains generated synthetic Atlas output and no FastAPI service, API token, OpenAI key, customer data or write endpoint. The human-decision UI exists only in the full local Next.js application and is unavailable on the static showcase. Protected local UI decisions also require a separate `PROGRAM_OS_UI_TOKEN` and signed session cookie; the static showcase never uses that token.

A live model call in the FastAPI prototype requires all three controls:

1. PROGRAM_OS_ENABLE_LIVE_AGENT=true
2. a valid OPENAI_API_KEY
3. PROGRAM_OS_API_TOKEN configured, with the caller presenting it as a bearer token

The default is:

~~~text
PROGRAM_OS_ENABLE_LIVE_AGENT=false
~~~

Possessing an OpenAI API key alone does not enable model calls.

The capability state can be checked at:

~~~text
GET /capabilities
~~~

Expected public deterministic behavior includes live_agent_enabled=false.

## Containerized local preview

Build and run both services:

~~~bash
docker compose up --build
~~~

Then open:

- UI: http://127.0.0.1:3000
- API health: http://127.0.0.1:8000/health
- API capabilities: http://127.0.0.1:8000/capabilities

The Compose file binds both published ports to 127.0.0.1. It is a **local preview configuration**, not an internet-facing deployment recipe.

Stop with:

~~~bash
docker compose down
~~~

## Deployment contract

A public showcase deployment must preserve these properties:

- synthetic Atlas data only;
- deterministic/static output wherever possible;
- PROGRAM_OS_ENABLE_LIVE_AGENT=false;
- no OpenAI key required;
- no customer or employer data;
- no production system-of-record credentials;
- no consequential write-back;
- audit output absent, ephemeral or isolated;
- no unauthenticated protected API;
- API and UI reproducible from the repository build.

## Production live-agent deployment

A future secured live-agent deployment is a different trust boundary.

Before enabling it:

- authenticate users through an enterprise identity path;
- authorize per tenant/project;
- propagate source permissions;
- store secrets in a managed secret store;
- isolate audit records by tenant;
- enforce gateway-level rate limits and abuse controls;
- log model/configuration versions;
- define evidence retention/deletion;
- review provider data-handling requirements;
- terminate TLS at a controlled ingress;
- ensure protected operations cannot be reached through a static showcase origin.

The prototype's bearer token and in-process rate limit are defense-in-depth for local/pilot use, not substitutes for production identity, authorization or gateway controls.

Do not enable the live-agent flag on the public showcase deployment.
