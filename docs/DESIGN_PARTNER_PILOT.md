# Design-partner pilot protocol

## Purpose

The V2 Atlas benchmark proves that Program OS can outperform a weak raw-context baseline on a controlled synthetic portfolio. It does not prove that the product creates useful decisions on real enterprise program data.

The design-partner pilot exists to test that external validity.

## Pilot question

Can Program OS identify material delivery risks, contradictions, and intervention opportunities early enough—and with enough evidence—to improve a real program manager's weekly operating decisions?

## Ideal pilot

Use one active program or portfolio with:

- 3–6 concurrent projects or workstreams;
- a weekly status cadence;
- current delivery artifacts;
- at least one meaningful dependency or resource constraint;
- at least one experienced program manager willing to review recommendations;
- no requirement for autonomous write-back.

A four-to-six-week historical window is useful because it gives enough evidence to compare forecasts against outcomes.

## Evidence boundary

Raw customer or employer data must not be committed to the public repository.

Use one of these patterns:

1. connected/private source accessible only during the pilot;
2. local evidence bundle excluded from Git;
3. customer-provided sanitized export;
4. syntheticized derivative created from the real failure pattern.

Only de-identified evaluation cases and aggregate pilot results belong in the public repository unless explicit permission says otherwise.

## Before analysis

Capture the program manager's current view before Program OS sees the evidence.

Record:

- official RAG;
- forecast expectation;
- top known risks;
- top dependencies;
- expected next milestone;
- current intervention priorities;
- unresolved decisions;
- confidence in the current plan.

This prevents hindsight from turning Program OS findings into things that were "obvious all along."

## Evidence snapshot

Freeze the evidence available at the analysis time.

For every source object preserve:

- source system;
- source ID;
- source-updated timestamp;
- retrieval timestamp;
- authority tier;
- related project/workstream;
- original observed value;
- permission context where available.

Program OS must be evaluated against what was knowable at that point in time.

## Evidence readiness gate

Before Program OS analysis, run the connector/export smoke command and retain the aggregate evidence-readiness result with the private pilot materials.

For a full portfolio pilot, prefer a **pilot_candidate** snapshot: complete ingestion, more than one source type, more than one project/workstream, and at least one authority-tier 1 or 2 source. A **connector_ready** result is sufficient to validate a single read-only connector, but it is not sufficient evidence that cross-source contradiction or portfolio-tradeoff behavior can be evaluated.

Review all readiness limitations before analysis, especially partial retrieval, missing permission context, stale records, weak authority mix, and single-source/single-project coverage.

The readiness profile validates structure and coverage. It does not establish organization-specific semantic mapping or compatibility with Atlas-specific detectors.

## Program OS run

Generate:

- official versus forecast RAG;
- confidence;
- contradictions;
- emerging risks;
- Monday intervention queue;
- recovery-plan credibility assessment;
- portfolio tradeoffs where applicable;
- evidence citations;
- missing information;
- what would change the conclusion.

Do not allow the system to establish official ground truth or perform consequential writes.

## Human review

For each material Program OS finding, the program manager records:

- **Accept** — correct and useful as stated;
- **Modify** — directionally useful but materially incomplete or wrong;
- **Reject** — incorrect or not useful;
- **Monitor** — plausible but not enough evidence yet.

Capture the rationale.

For recommendations also capture:

- action taken;
- action not taken;
- authority constraint;
- expected consequence;
- eventual outcome where observable.

## Metrics

### Safety / trust

- fabricated material facts: target 0;
- fabricated evidence IDs: target 0;
- unauthorized write attempts: target 0;
- high-confidence GREEN with a known mandatory blocker: target 0;
- material claims with valid evidence citations;
- explicit recognition of insufficient evidence.

### Detection

- material risks found before normal status reporting;
- material contradictions detected;
- missed known critical risks;
- false-alert rate.

### Judgment

- forecast RAG agreement with later outcome;
- confidence calibration;
- recovery-plan credibility accuracy;
- intervention urgency accuracy.

### Decision quality

- recommendation Accept / Modify / Reject / Monitor distribution;
- PM-rated usefulness;
- downstream consequences identified before action;
- resource/dependency tradeoffs surfaced correctly.

### Workflow value

- time to establish ground truth;
- time to prepare weekly status;
- number of manual source checks;
- number of issues escalated earlier than normal process;
- PM willingness to use the output in a real operating review.

## Pilot success criteria

A pilot is promising when all of the following are true:

- zero catastrophic trust failures;
- evidence citations are materially correct;
- at least one non-obvious material risk or contradiction is found early enough to change a decision;
- false alerts remain low enough that the Monday queue is usable;
- the PM judges at least one intervention recommendation as decision-useful;
- the system knows when it lacks enough evidence;
- the PM would choose to run the workflow again the following week.

Time savings alone are not enough. The product must improve decision quality or time-to-detection.

## Failure handling

Every meaningful failure becomes one of:

- case-specific context;
- retrieval defect;
- data-model defect;
- deterministic-rule defect;
- confidence/calibration defect;
- prompt/instruction defect;
- source-authority defect;
- new evaluation case;
- no system change because the case is exceptional.

Human disagreement is evidence, not automatically truth.

Global behavior changes require:

1. root-cause hypothesis;
2. proposed change;
3. offline evaluation;
4. review;
5. versioned deployment;
6. rollback path.

## Pilot readout

The final readout should answer:

- What did Program OS find that the current operating process missed?
- What did it get wrong?
- What was useful enough to act on?
- What created noise?
- What evidence was missing?
- Did the PM trust the result enough to use it in a real review?
- What would need to be true to pay for continued use?
- Should the project advance, narrow, or stop?

## Commercial validation question

Do not ask only whether the PM likes the product.

Ask whether the organization would pay to repeat the workflow across the portfolio if Program OS consistently finds material risks or contradictions before the current reporting process.


## Local pilot record tooling

Real pilot records can contain confidential program context. Keep them under
`var/pilots/`; `var/` is ignored by Git.

Create a local record:

```bash
python scripts/pilot_packet.py init \
  --pilot-id pilot-001 \
  --program-alias "Program A" \
  --output var/pilots/pilot-001.json
```

Before Program OS analysis, populate the `baseline` and `evidence_snapshot`
sections, run the applicable ingestion smoke/readiness check, then enforce the anti-hindsight gate:

```bash
python scripts/pilot_packet.py check-ready var/pilots/pilot-001.json
```

Validate the record:

```bash
python scripts/pilot_packet.py validate var/pilots/pilot-001.json
```

After human review, print a de-identified aggregate summary:

```bash
python scripts/pilot_packet.py summary var/pilots/pilot-001.json
```

The summary intentionally excludes finding text, rationales, and evidence IDs.

A structural example is available at
`examples/pilot/pilot-record-template.json`. It is a template, not real pilot
evidence.
