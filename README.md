# Program OS

**An evidence-grounded portfolio control and decision-intelligence system for program managers.**

Program OS sits above existing systems of record such as Jira, Confluence, meeting notes, testing systems, risk logs, calendars, and finance data. It reconciles conflicting operational evidence, forecasts delivery risk, prioritizes interventions across a portfolio, and preserves human accountability for consequential decisions.

## Status

**V1 — Product-definition MVP: published November 13, 2026.**

V1 defines the product contract, trust model, governance, architecture direction, evaluation strategy, and fictional Atlas Launch Program used for the evaluated prototype.

**V2 — Evaluated vertical slice: planned next.**

V2 will implement the first end-to-end Monday-to-Friday workflow against a synthetic five-workstream enterprise launch portfolio and a fixed golden evaluation set.

## The problem

Program managers rarely lack status information. They lack a reliable way to determine what is actually true, what is likely to happen next, and where intervention has the highest portfolio value.

Relevant evidence is fragmented across systems, frequently stale, sometimes contradictory, and often filtered through optimistic reporting. Small delivery signals can become launch-critical problems before official status changes.

Program OS is designed to answer:

- What changed?
- What evidence supports the current status?
- What evidence contradicts it?
- What is likely to happen before the next reporting cycle?
- Which issue deserves intervention first?
- What is the portfolio consequence of that intervention?
- What is still unknown?

## Product boundary

Program OS is **not** a replacement for Jira, Linear, Plane, Confluence, calendars, chat, or generic work-management software.

It does not aim to build issue tracking, Kanban boards, sprint management, document editing, calendars, chat, or a new system of record.

It consumes those systems, reasons across them, and returns controlled recommendations and actions.

## Weekly operating loop

### Monday

Program OS integrates available evidence, detects inconsistencies and emerging risks, evaluates forecast credibility, and generates a prioritized intervention list.

Priority is driven primarily by:

**Criticality × Probability × Impact × Time Sensitivity**

Confidence, authority, reversibility, evidence quality, and resource constraints modify the recommendation.

### During the week

Actions are resolved through new evidence, documented remediation, stakeholder alignment, or explicit human decisions. Completion of a task alone does not imply that the underlying risk is resolved.

### Thursday / Friday

Program OS produces an evidence-backed one-page status for each project: official RAG, forecast RAG, confidence, trend, top risks and dependencies, milestones, budget signal, launch date, and material changes since the prior report.

## Trust contract

Every material recommendation, forecast, status assessment, or alert must expose:

- conclusion;
- confidence;
- supporting evidence;
- evidence freshness;
- contradictions;
- assumptions;
- reasoning factors;
- what would change the conclusion.

Program OS prefers **insufficient evidence** over false certainty.

Official status remains a human accountability decision. The system can recommend, forecast, and challenge; it does not silently establish ground truth.

## Canonical V2 demo

Five projects appear mostly healthy by official reporting. Program OS detects that the evidence does not support that view.

It identifies an integration dependency slip, an optimistic recovery plan, an undocumented scope change, a shared-resource collision, and a worsening defect trend. It cites the conflicting sources, lowers confidence where evidence is incomplete, produces a forecast RAG distinct from official RAG, and recommends a portfolio intervention that protects a critical launch while showing the cost imposed on another project.

The program manager approves or overrides the recommendation. The decision and rationale are audited. Any proposed global behavior change becomes a governed learning proposal rather than an automatic model mutation.

## Architecture direction

~~~text
Systems of Record
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
        v
Deterministic Controls + Retrieval
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

The V2 implementation will start with one agent. Multi-agent orchestration is added only if evaluation results demonstrate a material benefit.

## Evaluation

V2 will compare an intentionally weak baseline against the Program OS architecture using the same golden test set.

Primary dimensions:

1. Safety and trust
2. Critical-risk and contradiction detection
3. Judgment quality
4. Decision quality

A high aggregate score cannot compensate for a catastrophic trust failure such as fabricated material evidence, a high-confidence GREEN despite a known mandatory blocker, or a consequential recommendation without evidence and tradeoffs.

## Repository map

- [Product requirements](docs/PRD.md)
- [Product principles](docs/PRODUCT_PRINCIPLES.md)
- [Architecture](docs/ARCHITECTURE.md)
- [Governance](docs/GOVERNANCE.md)
- [Evaluation strategy](docs/EVAL_STRATEGY.md)
- [PM skill model](docs/PM_SKILL_MODEL.md)
- [Competitive analysis](docs/COMPETITIVE_ANALYSIS.md)
- [Atlas synthetic program](examples/atlas/README.md)

## Release boundary

V1 documents what is designed. It does not claim that the V2 intelligence system is already implemented.

The project is a portfolio and learning prototype, not a production-certified autonomous business decision system.
