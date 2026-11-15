# Security policy

Program OS is currently an evaluated prototype, not a production-certified enterprise service.

## Public repository

Do not commit:

- API keys or access tokens;
- customer/employer artifacts;
- private Jira/Confluence exports;
- credentials;
- confidential evaluation data;
- production audit logs.

The public Atlas dataset is synthetic.

## Current security posture

The prototype uses read-only source-adapter contracts and has no autonomous consequential write path. The public demo path disables live model calls by default.

See [Production trust boundaries](docs/PRODUCTION_TRUST_BOUNDARIES.md) for the required architecture before real enterprise production use.

## Reporting

For this public prototype, report suspected security issues privately to the repository owner rather than publishing credential material or sensitive reproduction data in a public issue.
