# Architecture

**Status:** V1 design. The implementation described here is planned for the V2 evaluated prototype.

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

## V2 stack

- Python
- FastAPI
- OpenAI Agents SDK
- PostgreSQL + pgvector
- Pydantic
- lightweight React / Next.js interface
- Pytest
- Docker Compose

V2 will use synthetic source adapters rather than spending the first implementation cycle on production OAuth integrations.

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

## Deferred production concerns

The V2 prototype will document but not claim to solve:

- enterprise SSO and full RBAC;
- production Jira/Confluence OAuth;
- tenant isolation;
- secrets management at enterprise scale;
- production observability and SLOs;
- data retention policy;
- regional data residency;
- production disaster recovery;
- formal compliance certification.
