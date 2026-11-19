# Beta-readiness QA audit

**Audit date:** 2026-11-17  
**Baseline:** `main` after the V2.1 engineering-foundation work  
**Scope:** reviewer onboarding, local setup, hosted demo, protected override flow, Jira/JSON pilot ingestion, data handling, dependency posture, GitHub Actions, container behavior, and security boundaries.

## Release verdict

| Beta mode | Verdict | Boundary |
|---|---|---|
| Hosted synthetic Atlas review | **GO** | Safe for broad external distribution. Static, read-only, synthetic data only. |
| Local synthetic full-product review | **GO** | Safe for technical beta testers on localhost. Protected actions require a local bearer token. |
| Controlled real-data connector pilot | **GO WITH CONTROLS** | Run locally or in an approved private environment. Read-only ingestion/readiness only unless separately approved. |
| Self-serve real-data Monday → Friday product | **NO-GO** | Generic mapping, tenant isolation, SSO, managed secrets, durable audit and production authorization are not implemented. |
| Internet-facing deployment of the local API/UI | **NO-GO** | The repository intentionally provides a localhost prototype, not a production deployment recipe. |

## QA findings and disposition

### QA-01 — confidential Jira metadata could appear in public Actions history

**Severity:** High for a real design partner  
**Status:** Fixed

The repository is public. The Jira smoke workflow previously printed the aggregate readiness JSON and uploaded it as an artifact. It excluded issue content and issue IDs, but counts, source mix, freshness, and authority metadata can still be confidential.

Fix:

- Jira Actions workflow is explicitly sandbox/synthetic only;
- detailed readiness output is redirected to a runner-local file;
- the workflow prints only pass/fail after validation;
- the readiness file is deleted before job teardown;
- no readiness artifact is uploaded;
- real partner Jira ingestion is directed to a local/private environment.

### QA-02 — custom data directory could feed unauthenticated Atlas read endpoints

**Severity:** High if a tester repointed the API at private data  
**Status:** Fixed

The API supports `PROGRAM_OS_ATLAS_DIR`. The default synthetic Atlas endpoints are intentionally unauthenticated on localhost, but a custom directory should not inherit that behavior accidentally.

Fix:

- custom data is refused unless `PROGRAM_OS_ALLOW_CUSTOM_DATA_API=true`;
- custom data additionally requires `PROGRAM_OS_API_TOKEN` bearer authentication;
- Next.js sends that bearer token server-to-server only;
- the browser does not receive the token;
- regression tests cover blocked, unauthenticated, and authenticated custom-data cases.

This is a guardrail, not a statement that arbitrary customer data is supported by the Atlas-specific dashboard.

### QA-03 — connector identity metadata entered model context

**Severity:** Medium  
**Status:** Fixed

Normalized connector metadata can include principal identity, permission context, and human-readable source URLs. Those values are not required for the model's substantive reasoning.

Fix:

- `_connector` metadata is removed before evidence is rendered into model context;
- regression coverage verifies principal and source URL do not appear in rendered model evidence;
- documentation states that business payload content can still be sensitive and model use requires explicit organizational approval.

### QA-04 — Docker audit history was ephemeral

**Severity:** Medium for beta workflow integrity  
**Status:** Fixed

The container path previously wrote audit events inside the API container's `/tmp`, so removing/recreating the container could erase the local human-decision record.

Fix:

- Compose stores audit events in the named `program_os_audit` volume;
- API healthcheck is required before the web container starts;
- instructions show how to inspect the audit file and how to delete the volume after testing.

The local JSONL audit remains prototype storage; it is not WORM/tamper-evident production audit infrastructure.

### QA-05 — returning local testers could run stale web dependencies

**Severity:** Medium reliability  
**Status:** Fixed

`make demo` previously skipped `npm ci` whenever `web/node_modules` already existed, even if the lockfile changed.

Fix:

- the launcher fingerprints `package.json` plus `package-lock.json`;
- `npm ci` reruns only when the dependency fingerprint changes.

### QA-06 — accessibility regressions in evidence/decision feedback

**Severity:** Low  
**Status:** Fixed

- static evidence dialog now has the heading ID referenced by `aria-labelledby`;
- local decision receipt uses an ARIA live region so submission results are announced.

## Dependency/security review

Current pinned web versions were checked against the upstream security advisories available on 2026-11-17.

- Next.js `16.4.6` is newer than the November 2026 patched line `16.4.5` for the disclosed 16.4.x cache/response issues.
- React `19.3.1` is the patched 19.3.x release for the October 2026 React Server Components RCE.
- Pydantic `2.14.3` is newer than the 2.14.2 security-fix release for the October 2026 validation issues.
- FastAPI `0.163.1` is current in the audited lock set.
- Python dependencies are exact-locked; npm uses `package-lock.json`; Actions are pinned to full SHAs; Dependabot covers pip/npm/Docker/Actions.

Base container images still use mutable upstream tags rather than immutable digests. This is acceptable for the current local beta but should be tightened before a production release/reproducible supply-chain claim.

## Usability review

The supported reviewer path now has one entry point: [Beta testing Program OS](BETA_TESTING.md).

The guide separates:

1. hosted synthetic review — zero setup;
2. local synthetic full-product review — `make demo` or Docker;
3. controlled real-data connector pilot — local/private only.

The hosted review is the correct link to send broadly.

Real-data pilot instructions are intentionally more restrictive. That friction is a product/security requirement, not an onboarding defect.

## Remaining accepted risks

These are not blockers for the hosted/local synthetic beta, but they remain blockers for production or broad self-serve real-data use:

- no enterprise SSO;
- no tenant isolation or database row-level authorization;
- no production source-ACL enforcement;
- local/environment-variable secret handling rather than managed secrets;
- no production gateway/WAF/abuse controls;
- local JSONL audit is not tamper-evident/WORM;
- no customer retention/deletion control plane;
- no generic organization-specific source mapping/evaluation;
- live model calls can transmit normalized business evidence to the configured model provider when explicitly enabled;
- Docker base-image tags are not digest-pinned.

## Exit criteria for broad real-data beta

Do not broaden beyond controlled design partners until:

1. at least one real/sandbox Jira ingestion completes under the private/local workflow;
2. at least one experienced PM completes the design-partner protocol;
3. resulting failures are converted into de-identified/syntheticized evaluation cases;
4. no catastrophic trust or data-handling failure is observed;
5. the team decides whether production identity/tenancy work is justified by external validation.

## QA conclusion

Program OS is ready to send broadly for **synthetic product beta feedback** and ready for a **small, controlled real-data design-partner pilot** under the documented boundaries.

It is not ready to be described as a self-serve enterprise beta that users can connect to arbitrary company systems and operate as a production service.
