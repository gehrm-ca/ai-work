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

The local FastAPI prototype keeps read-only deterministic endpoints available without credentials, while human override and live-agent draft endpoints require PROGRAM_OS_API_TOKEN bearer authentication. Live agent calls additionally require an explicit PROGRAM_OS_ENABLE_LIVE_AGENT=true flag and OPENAI_API_KEY. Protected endpoints have a small in-process demo rate limit.

The Docker Compose preview binds published ports to 127.0.0.1 by default and is not an internet-facing deployment recipe.

These prototype controls do not provide enterprise SSO, tenant authorization, source ACL enforcement, managed secrets, durable audit storage or production abuse protection.

See [Production trust boundaries](docs/PRODUCTION_TRUST_BOUNDARIES.md) for the required architecture before real enterprise production use.

## Dependency and workflow hygiene

- Python direct dependencies are pinned.
- npm uses package-lock.json and npm ci.
- Dependabot monitors Python, npm, Docker and GitHub Actions dependencies.
- Third-party GitHub Actions are pinned to full commit SHAs in repository workflows.
- CI runs tests, builds the frontend and builds both containers.

## Reporting a vulnerability

Do not put credentials, private source data or sensitive reproduction material in a public issue.

Use GitHub's private vulnerability reporting flow from the repository Security tab when it is available. If that repository setting is not enabled, contact the repository owner privately through [Matt Gehrmann on LinkedIn](https://www.linkedin.com/in/mattgehrmann) and provide only the minimum information needed to establish a private reporting channel.

## Production disclaimer

A successful local demo, connector smoke test or synthetic evaluation does not establish production security. The controls listed as production blockers in [Production trust boundaries](docs/PRODUCTION_TRUST_BOUNDARIES.md) remain release gates.
