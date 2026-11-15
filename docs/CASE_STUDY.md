# Program OS — V2 case study

## The problem

Program managers usually have plenty of status information. The harder problem is deciding what is actually true, what is likely to happen next, and where intervention has the highest portfolio value.

Evidence is fragmented across delivery systems, plans, meeting notes, test reports, risk logs, finance data, and executive status. Those sources can be stale, contradictory, or optimistic.

Program OS is an evidence-grounded control and decision-intelligence layer over those systems of record.

## Product thesis

The core product claim is not “AI can summarize project data.”

It is:

> Program OS should detect material delivery risk before official reporting catches up, show the evidence, quantify uncertainty, expose contradictions, and recommend the highest-value intervention without taking accountability away from the program manager.

The canonical demo moment is:

> The dashboard says GREEN. Program OS says the evidence does not support GREEN yet — and shows exactly why.

## V2 vertical slice

V2 uses the fictional Atlas Launch Program: five interdependent workstreams preparing an AI-enabled enterprise workflow product for a regulated customer segment.

The synthetic portfolio contains 48 timestamped evidence artifacts, including Jira-style work items, risk entries, project pages, meeting notes, testing reports, decisions, retrospectives, budget snapshots, status reports, resource snapshots, a dependency map, and a milestone plan.

Planted scenarios include:

- a slipping external integration dependency;
- an optimistic recovery plan contradicted by historical performance;
- unapproved scope entering delivery;
- a shared-resource collision;
- a worsening defect trend;
- an approval bottleneck;
- contradictory executive and operational status.

## Architecture

Program OS intentionally starts with one structured AI analyst rather than a multi-agent runtime.

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
Structured AI Assessment
        |
        v
Human Approval / Override
        |
        v
Audit + Governed Learning Proposal
~~~

Deterministic logic handles hard constraints, provenance, confidence controls, and audit. The model handles ambiguous interpretation, reconciliation, risk inference, and recommendation.

Consequential project changes remain human-controlled.

## Evaluation-first development

The V2 benchmark was defined before final hardening.

Sixteen fixed cases test:

1. Safety and trust
2. Critical-risk and contradiction detection
3. Judgment quality
4. Decision quality

A weak baseline receives the raw Atlas portfolio context in one broad prompt.

Program OS adds targeted retrieval, deterministic evidence joins, structured output, citation validation, evidence-derived confidence, explicit RAG semantics, deterministic hard gates, and grounded signal augmentation.

Gold expectations are not included in either model prompt.

## Final measured result

Final benchmark configuration:

- model: `gpt-6.1-sol`
- OpenAI Agents SDK: `0.24.0`
- Program OS version: `0.2.0`
- dataset: `atlas-v2-001`
- cases: 16
- evaluated implementation commit: `0c84f439712a45eedb484d44f80682318138d9e0`

| Metric | Weak baseline | Program OS |
|---|---:|---:|
| Severity-weighted failure penalty | 60 | **3** |
| Cases with zero scored failures | 4/16 | **15/16** |
| Judgment failures | 9 | **1** |
| Detection failures | 3 | **0** |
| Decision Quality failures | 6 | **0** |
| Safety/Trust failures | 2 | **0** |
| Catastrophic failures | 0 | **0** |

This is a result on the synthetic Atlas benchmark. It is not a claim of equivalent performance on real enterprise portfolios.

## What the evals changed

The first measured runs exposed real defects rather than serving as a presentation metric.

They led to changes in:

- retrieval coverage for trends, approvals, resources, dependencies, scope, and status;
- confidence calibration;
- explicit RAG scope between milestone, project, and portfolio levels;
- deterministic signal augmentation;
- handling of resolved historical contradictions;
- scorer semantics for equivalent program-management language and negation.

The team stopped tuning with one known residual rather than optimizing the benchmark to zero.

## Known limitation

Case E14 expects GREEN after a formally approved scope reduction, baseline update, and stakeholder alignment. Program OS returns AMBER.

That conservative judgment remains disclosed in V2.

## Human accountability

Program OS separates:

- official RAG — accountable human status;
- forecast RAG — system prediction;
- confidence — evidence quality and completeness;
- recommendation — proposed intervention;
- override — human decision with rationale;
- learning proposal — governed change request, not automatic behavior mutation.

Overrides are evidence, not automatically truth.

## Why this matters

The product does not require an organization to replace Jira, Confluence, Azure DevOps, Smartsheet, or other systems of record.

Its value is the reasoning layer above them:

- reconcile evidence;
- find early warning signals;
- evaluate recovery credibility;
- expose cross-project tradeoffs;
- recommend intervention;
- preserve an auditable human decision trail.

## Five-minute review path

1. Run `make demo`.
2. Open the Atlas portfolio UI.
3. Compare official GREEN with forecast AMBER.
4. Review the Monday intervention queue.
5. Inspect evidence IDs behind contradictions and quality signals.
6. Review the cross-project resource tradeoff and its downstream cost.
7. Review the Friday status.
8. Read [V2 evaluation results](V2_EVALUATION_RESULTS.md) for the measured benchmark.
