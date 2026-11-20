# Production trust boundaries

**Status:** V2.1 architecture contract.  
**Purpose:** Define the security, tenancy, authorization, audit, and data-governance controls required before Program OS can operate on real enterprise data.

This document distinguishes controls already present in the prototype from controls that are mandatory before production use.

## Security objective

Program OS must never turn cross-system visibility into broader authority.

The system may only reason over evidence that the authenticated user and tenant are authorized to access. AI inference does not create new permissions.

The primary production rule is:

> Authorization happens before retrieval and before model context construction. The model never decides what the user is allowed to see.

## Trust-boundary diagram

~~~text
Enterprise Identity Provider
          |
          | authenticated identity + tenant
          v
+-----------------------------+
| Program OS AuthN / AuthZ    |
| deterministic policy        |
+-----------------------------+
          |
          | tenant-scoped request context
          v
+-----------------------------+         +----------------------+
| Source Adapter Layer        |-------->| Source Systems       |
| source permission checks    |         | Jira / Confluence /  |
+-----------------------------+         | testing / finance    |
          |                              +----------------------+
          | authorized source records only
          v
+--------------------------------------------------------------+
| Tenant-Isolated Evidence Store                               |
| immutable observations + source ACL/permission provenance    |
+--------------------------------------------------------------+
          |
          | tenant + permission constrained retrieval
          v
+-----------------------------+
| Deterministic Controls      |
| hard gates / policy / ACL   |
+-----------------------------+
          |
          | authorized evidence only
          v
+-----------------------------+         +----------------------+
| AI Assessment Boundary      |-------->| Model Provider       |
| no permission decisions     |         | approved data policy |
+-----------------------------+         +----------------------+
          |
          | recommendation / forecast
          v
+-----------------------------+
| Human Approval Boundary     |
+-----------------------------+
          |
          | approved action only
          v
+-----------------------------+
| Controlled Write Adapter    |
| future; separately scoped   |
+-----------------------------+
          |
          v
+--------------------------------------------------------------+
| Tenant-Isolated Audit + Decision History                     |
+--------------------------------------------------------------+
~~~

The public V2 demo does not include enterprise identity, tenant storage, or write adapters. Those are production blockers, not implied capabilities.

## Assets to protect

- source-system credentials and tokens;
- raw evidence and attachments;
- source-level permission metadata;
- normalized portfolio/project records;
- assessments and recommendations;
- human overrides and rationale;
- audit events;
- prompt/rule/model configuration;
- learning proposals;
- evaluation artifacts derived from private customer data.

## Threat model

| Threat | Failure mode | Required control |
|---|---|---|
| Cross-tenant retrieval | Evidence from Tenant A appears in Tenant B context | Tenant ID is mandatory on every durable object; retrieval requires server-derived tenant scope; no model-supplied tenant selectors |
| Permission widening | Program OS reads an object the user cannot access in the source system | Source adapters propagate source ACL/permission context; authorization filter runs before normalization/retrieval |
| Confused deputy | A privileged connector causes a lower-privilege user to see broad data | Connector service identity and end-user authorization are evaluated separately; effective access is the intersection |
| Prompt injection in source content | A Jira/Confluence record instructs the model to ignore controls or call tools | Source content is treated as untrusted data; system instructions/tool allowlists are outside evidence; source text cannot grant tool permissions |
| Secret leakage | API tokens appear in logs, prompts, exceptions, or audit | Managed secret store; redaction before logs/model context; never persist secrets in evidence |
| Unauthorized write | Model changes scope, status, budget, dates, risks, or source records | Read-only adapters by default; consequential writes require deterministic authorization plus explicit human approval |
| Audit tampering | Decision history is edited to hide prior state | Append-only audit storage; restricted write path; retention policy; integrity verification/versioning |
| Stale evidence presented as current | Old source state drives a confident recommendation | Preserve source_updated_at and retrieved_at; freshness affects confidence; surface stale/missing evidence |
| Silent partial ingestion | Permission/network errors look like “no issue exists” | Adapter returns explicit failures; partial coverage lowers confidence and is visible in the trust contract |
| Model-provider oversharing | Private evidence sent outside approved boundary | Provider/data-processing review, approved region/retention settings, minimization, tenant policy, redaction where required |
| Global behavior drift | Prompt/rule/model change silently alters decisions | Versioned configuration, offline eval, administrator approval, deployment record, rollback |
| Data-retention violation | Deleted/expired customer data remains in evidence or eval corpora | Tenant retention policy, deletion workflow, derivative-data review, audit of deletion execution |

## Tenant-isolation contract

Production storage must make tenant scope structural rather than conventional.

Every durable record must carry a non-null `tenant_id`, including:

- Evidence
- Project
- Portfolio
- Assessment
- Recommendation
- Override
- Audit Event
- Learning Proposal
- connector configuration
- evaluation case derived from private customer data

Required design:

1. Authentication resolves the user and tenant.
2. Server middleware creates an immutable request authorization context.
3. Data access APIs require that context; callers do not pass an arbitrary tenant ID.
4. Database queries include tenant scope by construction.
5. Retrieval indexes are partitioned or filtered deterministically by tenant before semantic/lexical ranking.
6. Model context is constructed only from already-authorized retrieval results.
7. Audit writes inherit tenant scope from the request context.
8. Cross-tenant administrator access, if ever supported, uses a separately audited elevated path.

A production release must include negative tests proving that Tenant A identifiers cannot retrieve Tenant B evidence.

## Source-permission propagation

A connector must not treat “the service account can read it” as “the user may see it.”

For each source object, preserve where available:

- source object ID;
- source tenant/site;
- source visibility/ACL;
- connector service identity;
- requesting user identity;
- effective permission result;
- source-updated timestamp;
- retrieval timestamp.

Effective access is the intersection of Program OS role permissions and source-system permissions.

If permission state cannot be established, the safe behavior is to exclude the object and report reduced coverage. It is not to assume access.

## RBAC matrix

Legend: **R** = read, **P** = propose, **A** = approve/execute within authority, **—** = not permitted.

| Capability | Program Manager | Workstream Owner | Executive Sponsor | Viewer | System Administrator |
|---|---:|---:|---:|---:|---:|
| Read authorized project evidence | R | R | R | R | R* |
| Add contextual evidence | A | A | — | — | — |
| Run assessment / forecast | A | A | A | — | A |
| Propose novel risk | P | P | — | — | — |
| Accept/modify project risk | A | P | A where authority applies | — | — |
| Override recommended RAG | A | P | A where authority applies | — | — |
| Change official committed scope/date | P | P | A per org authority | — | — |
| Send executive status | A | — | A | — | — |
| Approve material budget/risk acceptance | P | — | A | — | — |
| Change global prompt/rules/scoring | — | — | — | — | A |
| Approve global AI behavior change | — | — | — | — | A |
| Read cross-tenant data | — | — | — | — | — by default |

* System Administrator access to customer content is not implied by configuration authority. Production should separate platform administration from customer-data access wherever possible.

## Consequential-write boundary

V2/V2.1 source adapters are read-only.

A future write adapter must require all of:

1. authenticated user;
2. tenant scope;
3. source-system permission;
4. Program OS role permission;
5. action-specific authority check;
6. explicit human approval for consequential actions;
7. before-state snapshot;
8. idempotency key;
9. executed-write result;
10. append-only audit event.

The model may compose a proposed action. It must not possess an unrestricted source-system write tool.

Human-only actions remain human-only, including compliance waivers, acceptance of material business risk, and major budget approvals.

## Model-provider boundary

Before private enterprise evidence is sent to a model provider, production deployment must define:

- approved provider/model list;
- contractual data-processing terms;
- retention/training policy;
- permitted data classifications;
- regional/data-residency requirements;
- encryption in transit;
- prompt/evidence minimization;
- redaction/tokenization requirements;
- incident-response path.

Model selection is therefore both a quality decision and a data-governance decision.

## Prompt-injection boundary

Operational source content is untrusted.

Controls:

- evidence text cannot modify system instructions;
- evidence cannot grant tool permissions;
- tool schemas and authorization are deterministic application controls;
- source-provided URLs are not automatically fetched;
- instructions embedded in evidence are treated as quoted data;
- tool outputs are revalidated against tenant/source permissions;
- consequential actions remain behind approval gates.

## Secrets

Production credentials belong in a managed secret store, not:

- Git;
- evidence payloads;
- prompts;
- audit records;
- model outputs;
- client-side environment variables.

Required controls:

- least-privilege connector scopes;
- rotation;
- expiry where supported;
- separate credentials by environment;
- access logging;
- immediate revocation path.

## Audit integrity

A material assessment or action must be reconstructable.

Audit records should include:

- tenant;
- actor;
- role;
- action;
- target;
- before/after;
- evidence snapshot IDs;
- source freshness;
- model/version;
- prompt/rule version;
- deterministic control version;
- approval/rationale;
- timestamp;
- execution result.

Production audit storage should be append-only from the application perspective and protected by stricter permissions than ordinary operational records.

## Retention and deletion

Production must define separate retention for:

- source evidence snapshots;
- assessments/recommendations;
- audit records;
- model traces;
- evaluation cases;
- derived/syntheticized cases.

Customer deletion must address derivatives. A private failure case may not be copied into the public evaluation corpus merely because identifiers were removed; it must be reviewed for re-identification/confidentiality risk.

## Global AI behavior changes

System-wide behavior changes remain administrator-controlled.

Required lifecycle:

1. triggering evidence/cases;
2. root-cause hypothesis;
3. proposed change;
4. offline evaluation;
5. regression review;
6. human administrator approval;
7. versioned deployment;
8. monitoring;
9. rollback.

The system must be able to answer which model, prompt/rule version, deterministic-control version, and evidence snapshot produced a recommendation.

## Implemented now

V2/V2.1 currently implements or demonstrates:

- immutable evidence observations;
- source IDs and timestamps;
- read-only adapter contract;
- explicit partial/permission failure states;
- single-agent reasoning behind deterministic controls;
- citation validation;
- explicit confidence;
- deterministic hard gates;
- human override;
- append-only local audit semantics;
- governed learning proposals;
- explicit live-agent feature gate for the public demo;
- no autonomous consequential write path.

## Production blockers

The prototype does **not** yet claim:

- enterprise SSO;
- production tenant isolation;
- database row-level security;
- source ACL enforcement against a real vendor;
- managed secrets infrastructure;
- production append-only/WORM audit storage;
- customer-configurable retention/deletion;
- regional data residency;
- production model-provider governance;
- disaster recovery;
- formal security/compliance certification.

These are release blockers for enterprise production use, not backlog polish.

## Production security release tests

At minimum, production CI/evaluation must prove:

- Tenant A cannot retrieve Tenant B evidence by ID, search, embedding similarity, or tool call.
- A user cannot retrieve source objects outside effective source permissions.
- A connector permission error is surfaced as incomplete coverage.
- A prompt-injected source record cannot alter tool authorization.
- An API key or model credential never appears in logs or returned evidence.
- A model cannot execute a consequential write without approved authorization context.
- Audit records preserve the original recommendation and human decision.
- Global AI behavior cannot change without a versioned approved deployment.

## November 2026 local-preview hardening

The local Next.js preview now uses a separate UI token and expiring HttpOnly session cookie for protected operations and custom-data pages. This is a local single-operator guard and **not** enterprise authentication or source-level RBAC. API calls are additionally subject to local request and model-call quotas, not billing-level spend guarantees. The local audit includes hash-chain checks but remains rewritable by anyone controlling the underlying file. No production blockers above are removed by these prototype safeguards.

The live evaluation workflow now validates its model input through an environment variable rather than interpolating user input into shell source. Container images run without root privileges and drop unnecessary Linux capabilities in Compose. Digest pinning remains pending verified registry digests.
