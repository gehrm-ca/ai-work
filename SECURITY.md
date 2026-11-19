# Security policy

Program OS is currently an evaluated prototype, not a production-certified enterprise service.

## Public repository

Do not commit:

- API keys or access tokens;
- customer/employer artifacts;
- private Jira/Confluence exports;
- credentials;
- confidential evaluation data;
- production audit logs or model traces.

The public Atlas dataset is synthetic. Local environment files, var/ and artifacts/ are gitignored, but users remain responsible for files stored elsewhere.

## Current security posture

The prototype uses read-only source-adapter contracts and has no autonomous consequential write path.

The public GitHub Pages showcase is static and deterministic.

The local FastAPI prototype keeps the default synthetic Atlas read-only endpoints available without credentials. If a custom `PROGRAM_OS_ATLAS_DIR` is configured, the API refuses it unless `PROGRAM_OS_ALLOW_CUSTOM_DATA_API=true` is explicitly set, and custom-data endpoints then require `PROGRAM_OS_API_TOKEN` bearer authentication. Human override and live-agent draft endpoints also require PROGRAM_OS_API_TOKEN bearer authentication. The full local Next.js UI can submit human overrides only through a same-origin server-side proxy after authenticating with a separate 32+ character `PROGRAM_OS_UI_TOKEN` and an eight-hour signed HttpOnly cookie. The backend bearer token is read from the server environment and is not sent to browser code. With custom-data API mode on, Next.js private pages also require that local UI session; if a UI token is missing, they fail closed. Live agent calls additionally require an explicit PROGRAM_OS_ENABLE_LIVE_AGENT=true flag and OPENAI_API_KEY. Connector principal/permission/source-URL metadata is stripped before model context construction, but normalized business evidence can still be sent to the configured model provider. Protected endpoints have a small in-process demo rate limit and a per-process live-agent call quota. Neither is a guaranteed monetary cap: project-level provider spend controls must be configured separately. Live-agent drafts undergo citation-ID validation, but they are not finalized assessments. Local audit JSONL records have a verification hash chain, which does not make the file immutable or immune to full-history rewriting.

The Docker Compose preview binds published ports to 127.0.0.1 by default and is not an internet-facing deployment recipe. Docker audit events persist in a named local volume until the tester explicitly removes it.

These prototype controls do not provide enterprise SSO, tenant authorization, source ACL enforcement, managed secrets, durable audit storage or production abuse protection.

See [Production trust boundaries](docs/PRODUCTION_TRUST_BOUNDARIES.md) for the required architecture before real enterprise production use.

## Dependency and workflow hygiene

- Python direct dependencies are pinned.
- npm uses package-lock.json and npm ci.
- Dependabot monitors Python, npm, Docker and GitHub Actions dependencies.
- Third-party GitHub Actions are pinned to full commit SHAs in repository workflows.
- A high-confidence credential-pattern scanner runs against tracked source in CI. A full local history scan can be run with `python scripts/security_scan.py --history`.
- CI runs tests, builds the frontend and builds both containers.
- The public-repository Jira Actions workflow is limited to sandbox/synthetic use and does not retain its readiness summary as a public artifact.

## Reporting a vulnerability

Do not put credentials, private source data or sensitive reproduction material in a public issue.

Use GitHub's private vulnerability reporting flow from the repository Security tab when it is available. If that repository setting is not enabled, contact the repository owner privately through [Matt Gehrmann on LinkedIn](https://www.linkedin.com/in/mattgehrmann) and provide only the minimum information needed to establish a private reporting channel.

## Production disclaimer

A successful local demo, connector smoke test or synthetic evaluation does not establish production security. The controls listed as production blockers in [Production trust boundaries](docs/PRODUCTION_TRUST_BOUNDARIES.md) remain release gates.
