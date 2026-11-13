# Governance and Human Accountability

## Core rule

Program OS may learn continuously, but it may not silently change its own consequential decision behavior.

The same philosophy applies to project decisions:

**No consequential project change without human approval.  
No consequential global AI behavior change without human approval.**

## Roles

### Program Manager

May inspect evidence, resolve project actions, update remediation, accept or reject proposed novel risks, and override Program OS recommendations with documented rationale.

### Team Lead / Workstream Owner

May contribute evidence and context, update assigned workstream information, and propose corrections.

### Executive Sponsor

May view portfolio status and approve material decisions according to organizational authority.

### Viewer / Stakeholder

Read-only.

### System Administrator

Controls global AI behavior changes, including decision rules, prompts, scoring, source hierarchy, confidence behavior, and other system-wide policies.

## Consequential-action boundary

Program OS can automatically ingest, detect, assess, draft, and monitor.

It can recommend scope, schedule, owner, mitigation, escalation, and portfolio resource changes.

Human approval is required for:

- official RAG changes;
- committed scope changes;
- launch-date changes;
- material budget changes;
- closure of major risks;
- externally distributed executive status.

Compliance waivers, acceptance of material business risk, and major budget approvals remain human-only.

## Override contract

An override stores:

- original system recommendation;
- human decision;
- rationale;
- missed evidence or context;
- exception versus possible reusable rule;
- expected downside if the override is wrong;
- actor;
- timestamp;
- before/after state;
- later outcome.

Overrides do not automatically train or update the system.

## Novel-risk workflow

An AI-discovered risk is a proposal, not official ground truth.

Allowed states:

- **Accept** — establish as an official risk with owner and response.
- **Modify** — correct description, probability, impact, or interpretation.
- **Reject** — dismiss with rationale.
- **Monitor** — retain as an emerging signal pending more evidence.

## Governed learning loop

1. Observe outcome or human feedback.
2. Capture the case.
3. Diagnose the likely failure mode.
4. Propose a system change.
5. Run offline evaluation against existing golden cases.
6. Review regressions.
7. Require System Administrator approval.
8. Deploy as a versioned change.
9. Monitor.
10. Roll back if necessary.

A System Improvement Proposal should record:

- triggering cases;
- original conclusion;
- human conclusion;
- eventual outcome;
- failure category;
- root-cause hypothesis;
- proposed change;
- expected improvement;
- possible regressions;
- evaluation result;
- approver;
- effective version and date;
- rollback path.

## Trust contract

No material RAG, forecast, intervention, or alert should exist without an evidence trail.

The UI should expose:

- conclusion;
- confidence;
- evidence;
- freshness;
- contradictions;
- assumptions;
- reasoning factors;
- what would change the conclusion.

The product should prefer an explicit unknown over an unsupported confident answer.
