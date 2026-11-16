# Architecture

**Status:** V2 evaluated prototype implemented; V2.1 external-validation and production-boundary work in progress.

## System shape

~~~text
Existing Systems of Record
(Jira, Confluence, meetings, testing, risk, finance)
                 |
                 v
          Source Adapters
                 |
                 v
      Immutable Evidence Layer
                 |
                 v
       Canonical Program Model
                 |
        +--------+---------+
        |                  |
        v                  v
Deterministic Controls   Retrieval
        |                  |
        +--------+---------+
                 |
                 v
      AI Assessment / Recommendation
                 |
                 v
          Human Approval
                 |
                 v
        Audit + Learning Proposal
~~~

## Implemented V2/V2.1 stack

- Python 3.12
- FastAPI
- OpenAI Agents SDK
- Pydantic
- file-backed synthetic Atlas evidence
- read-only Jira Cloud adapter for V2.1 external-validation work
- React / Next.js interface
- Pytest
- Docker Compose
- GitHub Actions and GitHub Pages

PostgreSQL + pgvector remain a **target persistence/retrieval direction**, not part of the shipped V2 prototype. The evaluated V2 benchmark uses the repository-backed Atlas dataset and in-process retrieval logic.

V2 began with synthetic source adapters; V2.1 now includes a read-only Jira Cloud connector, while production OAuth UX and enterprise persistence remain out of scope.

## Architectural boundary

Program OS is not the source of truth for project execution. Existing systems remain authoritative for their native records.

Program OS stores:

- normalized program entities;
- immutable evidence observations;
- versioned assessments;
- recommendations;
- human decisions and overrides;
- audit events;
- learning proposals;
- evaluation outcomes.

## Evidence and time

Evidence observations are immutable.

If a source says a milestone is due November 18 at one point in time and later changes to November 22, both observations should remain reconstructable.

This permits questions such as:

- What did the system know when it made this recommendation?
- Which source changed afterward?
- Was the forecast wrong, or did the plan change?
- Did a human override outperform the system recommendation?

## Deterministic versus AI responsibilities

### Deterministic controls

Use code for:

- date comparisons;
- mandatory gate checks;
- permissions;
- audit recording;
- explicit severity thresholds;
- source metadata;
- system versions;
- formal calculations;
- release-gate tests.

### AI reasoning

Use the model for:

- interpreting ambiguous text;
- reconciling evidence without inventing certainty;
- identifying possible emerging risks;
- assessing recovery-plan credibility;
- explaining tradeoffs;
- synthesizing recommendations and status.

The model does not get to bypass deterministic controls.

## Single-agent-first

V2 starts with one agent plus tools.

Specialized or multi-agent orchestration is added only when a controlled evaluation shows a meaningful gain in reliability, quality, latency, or cost.

## Canonical entities

Portfolio, Project, Milestone, Work Item, Dependency, Risk, Issue, Scope Item, Change, Decision, Stakeholder, Resource, Quality Signal, Action, Evidence, Assessment, Recommendation, Override, Audit Event, and Learning Proposal.

## Recommendation record

A material recommendation should carry:

- system version;
- model and prompt/rule version where applicable;
- evidence snapshot;
- timestamp;
- conclusion;
- confidence;
- assumptions;
- contradictions;
- expected impact;
- alternatives considered;
- approval requirement.

## V2 vertical slice

The first end-to-end path is:

1. load Atlas synthetic evidence;
2. normalize entities and provenance;
3. retrieve evidence for a portfolio assessment;
4. apply deterministic RAG constraints;
5. produce structured forecast and confidence;
6. identify contradictions and emerging risks;
7. recommend one portfolio intervention;
8. allow PM approval or override;
9. record audit history;
10. generate Friday status;
11. run the same scenario through the golden eval suite.

## Production trust boundary

The production security contract is defined in [Production trust boundaries](PRODUCTION_TRUST_BOUNDARIES.md).

The current prototype does not claim enterprise SSO, tenant isolation, source ACL enforcement against real vendor systems, managed secrets, production audit storage, customer retention/deletion controls, regional data residency, disaster recovery, or formal certification.
