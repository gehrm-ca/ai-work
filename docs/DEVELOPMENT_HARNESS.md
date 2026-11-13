# V2 Development Harness

## Purpose

This harness is for **building Program OS**, not for changing the Program OS runtime architecture.

The product remains single-agent-first. The development workflow may use multiple coding/research agents because the workstreams are separable and can be evaluated independently.

## Operating model

One orchestrator coordinates four parallel lanes and one integration gate.

### Lane A — Atlas data

Owns synthetic portfolio artifacts, provenance, timestamps, intentional contradictions, and the gold manifest.

### Lane B — Evals and baseline

Owns the fixed golden cases, weak baseline, scoring, catastrophic-failure gates, and comparison report.

### Lane C — Core engine

Owns canonical models, immutable evidence, deterministic controls, confidence inputs, audit objects, and unit tests.

### Lane D — Decision workflow and demo

Owns retrieval, grounded assessment, forecast RAG, contradiction handling, portfolio recommendations, override flow, Friday status, and the minimal UI/API path.

### Gatekeeper — Reviewer / integrator

Owns:
- architecture consistency;
- cross-lane interface compatibility;
- test/eval evidence;
- trust-contract enforcement;
- merge readiness;
- release-claim accuracy.

The gatekeeper must reject a change that makes the demo look better by weakening evidence, uncertainty, audit, or evaluation requirements.

## Durable state

GitHub is the source of truth for development state.

Each autonomous run should read:
1. `README.md`
2. `docs/PRD.md`
3. `docs/PRODUCT_PRINCIPLES.md`
4. `docs/ARCHITECTURE.md`
5. `docs/GOVERNANCE.md`
6. `docs/EVAL_STRATEGY.md`
7. the assigned GitHub issue

The agent should then inspect the current code and tests before changing anything.

## Agent contract

Every implementation agent receives:

### Goal
The assigned GitHub issue.

### Constraints
- do not broaden MVP scope;
- do not add generic PM features;
- do not weaken the trust contract;
- do not invent production capabilities;
- keep Program OS runtime single-agent-first;
- prefer deterministic code for deterministic logic;
- preserve immutable evidence and versioned interpretation;
- add tests for behavior changed.

### Required output
- code/data/docs changes;
- tests or eval cases;
- a concise implementation note;
- unresolved risks or assumptions;
- evidence that acceptance criteria were met.

## Work decomposition rule

Use parallel agents only when tasks are independent.

Good parallel work:
- generate different groups of Atlas artifacts;
- write eval cases while core models are implemented;
- review deterministic rules while UI scaffolding is built;
- inspect separate failure modes.

Keep dependent work serial:
- schema changes followed by code depending on those schemas;
- migrations that touch the same models;
- two agents editing the same file;
- evaluation after a behavior-changing merge.

## Branch and integration pattern

Recommended branch names:

- `v2/atlas-data`
- `v2/evals-baseline`
- `v2/core-engine`
- `v2/decision-workflow`
- `v2/demo`

Each lane should produce small commits tied to its issue.

The gatekeeper integrates only after:
1. tests pass;
2. golden cases are unchanged unless the change is itself an approved eval correction;
3. catastrophic trust gates pass;
4. new output is evidence-grounded;
5. README/docs accurately describe implementation status.

## Evaluation-before-optimization loop

For every material intelligence change:

1. run the existing golden suite;
2. record baseline metrics;
3. make one coherent change;
4. rerun the suite;
5. inspect regressions, not only aggregate score;
6. retain the change only if it improves the intended behavior without violating catastrophic gates.

Do not move the gold standard to make the implementation look better. A gold-case correction must be explicit and justified.

## Weekend V2 sequence

### Stage 1
Atlas data + golden cases + weak baseline.

### Stage 2
Canonical model + immutable evidence + deterministic controls.

### Stage 3
Grounded single-agent assessment workflow.

### Stage 4
Monday actions + portfolio tradeoff + PM override + audit + Friday status.

### Stage 5
Run baseline vs Program OS evaluation and fix catastrophic failures.

### Stage 6
Minimal demo surface and release documentation.

## Stop conditions

An autonomous run should stop and surface the issue rather than improvise when:
- a change would weaken a locked product principle;
- two sources of truth conflict and no rule defines precedence;
- a consequential behavior lacks a test/eval case;
- credentials or secrets would be required;
- a change would introduce confidential data;
- a production claim cannot be supported by implementation evidence.

## Definition of done

V2 is ready only when the fixed eval suite and five-minute demo prove the vertical slice described in the PRD.

A polished UI without that evidence is not V2.
