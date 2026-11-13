# Program OS Product Requirements Document

**Status:** V1 product-definition MVP  
**Date:** November 13, 2026

## 1. Product definition

Program OS is an evidence-grounded portfolio control and decision-intelligence system for program managers responsible for several concurrent enterprise projects or workstreams.

It operates as an intelligence layer over existing systems of record. It continuously reconciles operational evidence, identifies emerging delivery risks and contradictions, evaluates the credibility of recovery plans, prioritizes interventions across the portfolio, drafts executive status, and preserves human accountability.

## 2. Primary user

The primary user is a program manager responsible for roughly three to six concurrent enterprise projects or workstreams.

The user is accountable for weekly readiness, stakeholder alignment, risk and dependency management, status reporting, and tradeoffs involving scope, schedule, resources, and escalation. Exact decision rights vary by organization.

## 3. Core problem

Program decisions are made from fragmented evidence with different freshness, authority, and reliability.

Common failure modes include:

- optimistic team reporting;
- stale executive status;
- lagging risk registers;
- late requirements;
- unexpectedly difficult technical work;
- defect trends discovered after the plan assumes readiness;
- unrecorded scope changes;
- cross-project resource contention;
- recovery plans that are possible in theory but inconsistent with prior execution.

The product must help the PM determine what is true, what is uncertain, what is likely to happen, and what intervention matters most.

## 4. Goals

Program OS must:

1. reconcile evidence across heterogeneous sources;
2. expose contradictions instead of silently resolving them;
3. distinguish official status from forecast status;
4. identify emerging risks before official RAG changes;
5. evaluate the credibility of plans and recovery claims;
6. prioritize intervention across the portfolio;
7. model collateral consequences of portfolio tradeoffs;
8. generate evidence-backed Monday actions and Thursday/Friday status;
9. support human override with rationale and auditability;
10. learn from outcomes without silently changing system behavior.

## 5. Non-goals

The MVP will not build:

- issue tracking;
- Kanban boards;
- sprint management;
- document editing;
- calendars;
- chat;
- generic work management;
- autonomous compliance waivers;
- autonomous acceptance of material business risk;
- autonomous budget approval;
- self-modifying global decision behavior.

## 6. Weekly operating model

### Monday control cycle

The system:

1. ingests current evidence;
2. compares it with the prior evidence snapshot;
3. identifies schedule slippage, scope change, defect trends, dependency threats, resource conflicts, overdue decisions, and inconsistent status;
4. evaluates recovery-plan credibility;
5. generates a prioritized intervention list;
6. identifies discrepancies that require the PM to establish ground truth.

Each Monday action contains:

- issue or risk;
- project;
- impact;
- probability;
- recommended next step;
- evidence;
- confidence.

Priority is primarily:

**Criticality × Probability × Impact × Time Sensitivity**

Secondary modifiers include evidence confidence, decision authority, reversibility, strategic importance, resource constraints, committed obligations, and cost of intervention.

### During the week

An action may be resolved by documented remediation, corrected source evidence, stakeholder alignment, an approved decision, or evidence that the risk no longer applies.

A checked task is not by itself proof that the underlying risk is resolved.

### Thursday / Friday reporting

For each project, Program OS drafts:

- project and goal;
- key stakeholders;
- timeline and launch date;
- official RAG;
- forecast RAG;
- confidence;
- trend;
- top risks and dependencies;
- next milestone;
- budget signal;
- changes since the prior report;
- unresolved contradictions or unknowns.

## 7. Evidence model

Evidence is immutable. Interpretations are versioned.

Every evidence object must retain enough provenance to reconstruct what the system knew at the time of a recommendation:

- source;
- source object ID;
- observed value or extracted fact;
- source-updated timestamp;
- retrieval timestamp;
- authority tier;
- related program entities.

The system must preserve earlier observations when a source later changes.

Source hierarchy in the MVP:

1. operational systems such as Jira, risk logs, and maintained project documentation;
2. team and automated systems such as meeting notes, testing, calendar, retrospectives, and plans;
3. lagging executive status and budget summaries.

Hierarchy is not an automatic truth rule. Freshness, directness, authority, and contradiction must remain visible.

## 8. Canonical entities

The MVP model includes:

- Portfolio
- Project / Workstream
- Milestone
- Work Item
- Dependency
- Risk
- Issue
- Scope Item
- Change
- Decision
- Stakeholder
- Resource
- Quality Signal
- Action
- Evidence
- Assessment
- Recommendation
- Override
- Audit Event
- Learning Proposal

## 9. Status model

Program OS maintains two separate states:

**Official RAG** — accountable human status used for reporting.

**Forecast RAG** — Program OS assessment of where the project is heading based on current evidence.

Forecast output also includes confidence and trend: improving, stable, or deteriorating.

## 10. Hybrid RAG engine

The RAG engine combines deterministic controls with AI interpretation.

Deterministic controls establish hard boundaries. Examples:

- missing mandatory approval cannot produce GREEN;
- unresolved launch-critical blocker produces RED;
- a critical dependency forecast beyond the committed launch date with no viable mitigation produces RED;
- material required evidence missing caps confidence;
- conflicting authoritative evidence reduces confidence and generally blocks a confident GREEN.

AI reasoning evaluates ambiguous evidence inside those boundaries, such as defect severity, workaround credibility, stakeholder context, or whether recovery assumptions are realistic.

The engine exposes:

1. constraint checks;
2. evidence assessment;
3. forecast assessment;
4. final recommended RAG.

## 11. Confidence model

User-facing confidence is banded:

- High
- Moderate
- Low

Confidence is derived from explicit factors rather than model self-confidence:

**Evidence Quality × Source Agreement × Freshness × Coverage × Historical Reliability**

The implementation may maintain an internal numeric score for ranking and evaluation, but V2 will not present calibrated percentages until there is evidence that those percentages are meaningful.

Missing mandatory evidence caps confidence.

## 12. Forecast credibility

Program OS does not replace team estimates. It evaluates their credibility.

The product distinguishes:

1. plan estimate;
2. reliability evidence;
3. confidence-adjusted forecast.

Inputs may include historical milestone reliability, similar-task performance, team composition changes, dependency status, remaining scope, defect trend, prior recovery-plan success, and resource availability.

Historical performance is a credibility modifier, not a mechanical haircut to every estimate.

## 13. Escalation model

Four levels:

1. **Monitor** — weak signal; gather evidence.
2. **Monday Action** — credible emerging issue requiring intervention.
3. **Immediate Alert** — high-probability critical threat that cannot wait.
4. **Executive Decision Required** — material decision exceeds PM authority.

Escalation is based on projected consequence and time sensitivity, not merely current RAG.

## 14. Novel-risk workflow

AI-discovered risks use four states:

- Accept
- Modify
- Reject
- Monitor

The AI may propose a risk with confidence, evidence, possible impact, and recommended validation. It may not silently add an inferred risk to the official risk register.

**AI can discover and propose. Humans establish ground truth.**

## 15. Roles and authority

### Program Manager

Full project access; resolve issues; update remediation plans; override recommended status with rationale.

### Team Lead / Workstream Owner

Update workstream evidence; add context; propose corrections and changes.

### Executive Sponsor

Portfolio and status view; approve major scope, schedule, or budget decisions according to organizational authority.

### Viewer / Stakeholder

Read-only.

### System Administrator

Approve global changes to decision rules, prompts, scoring, source hierarchy, confidence behavior, or other system-wide AI behavior.

## 16. Autonomy boundary

Program OS may automatically:

- ingest evidence;
- detect discrepancies;
- calculate assessments;
- draft Monday actions;
- draft status;
- update evidence links;
- resolve an action when documented resolution criteria are met.

It may recommend:

- scope changes;
- schedule changes;
- owner changes;
- mitigation;
- escalation;
- portfolio resource moves.

Human approval is required for official RAG changes, committed scope, launch dates, material budget changes, closure of major risks, and externally distributed executive status.

Compliance waivers, acceptance of material business risk, and major budget approvals remain human-only.

## 17. Overrides and audit

A PM override records:

- original system recommendation;
- new human status or decision;
- rationale;
- evidence or context the system missed;
- whether the case is a one-time exception or candidate general rule;
- expected consequence if the override is wrong;
- actor;
- timestamp;
- before and after state;
- later edits or reversals.

Override does not equal truth. Outcome evidence determines what should be learned.

## 18. Governed learning

Program OS may learn continuously, but may not silently change its own decision behavior.

Learning flow:

Observed outcome or feedback → captured learning → root-cause diagnosis → proposed system change → offline evaluation → human approval → versioned deployment → monitoring → rollback if needed.

Global behavior changes require System Administrator approval.

Every material recommendation should be attributable to a system version.

## 19. Trust contract

Every material recommendation, status, forecast, or alert must expose:

- conclusion;
- confidence;
- evidence;
- freshness;
- contradictions;
- assumptions;
- reasoning factors;
- what would change the conclusion.

When evidence is insufficient, the system should say so.

## 20. V1 acceptance criteria

V1 is complete when the repo clearly defines:

- product thesis;
- MVP scope and non-goals;
- Monday-to-Friday loop;
- PM skill model;
- official vs forecast RAG;
- escalation and intervention rules;
- human approval and override model;
- audit and governed learning;
- competitive differentiation;
- architecture direction;
- initial eval strategy.

## 21. V2 acceptance criteria

The evaluated prototype must demonstrate that it can:

- detect at least four of five planted portfolio risks;
- avoid unsupported material facts;
- cite evidence for every material recommendation;
- detect at least one cross-source contradiction;
- produce forecast RAG distinct from official RAG;
- reduce confidence when evidence is stale, incomplete, or conflicting;
- evaluate one recovery plan against historical performance;
- identify one cross-project resource or dependency conflict;
- recommend one portfolio intervention with downstream consequences;
- generate the Monday action list;
- generate the Thursday/Friday status;
- support PM override and audit;
- create a learning proposal without automatically changing global behavior.

## 22. Canonical V2 scenario

The fictional Atlas Launch Program contains five workstreams:

1. Application & UX
2. Platform & Integrations
3. Data / AI
4. Security, Compliance & Testing
5. Commercial Launch & Operations

The synthetic evidence set will contain approximately 40–50 timestamped artifacts with deliberate contradictions, stale data, latent risk signals, and portfolio tradeoffs.

## 23. Release principle

A feature does not count as working if Program OS cannot explain why it believes something, show the evidence, expose uncertainty, and defer when evidence is insufficient.
