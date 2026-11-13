# Evaluation Strategy

## Objective

Program OS is evaluated on decision reliability, not whether its prose sounds intelligent.

V2 will use a fixed golden evaluation set before architecture optimization.

## Golden set

Target: 15–20 cases.

Each case specifies:

- input evidence;
- expected official/forecast behavior;
- expected confidence band;
- expected risks and contradictions;
- expected escalation level;
- acceptable recommendation characteristics;
- evidence that must be cited;
- facts the system must not invent;
- conditions where the correct result is insufficient evidence.

## Baseline comparison

V2 will run two approaches against the same cases.

### Weak baseline

- one model call;
- large raw portfolio context;
- no targeted retrieval;
- no deterministic RAG controls;
- no explicit provenance enforcement;
- no dedicated contradiction logic;
- no evidence-derived confidence control.

### Program OS

- canonical data model;
- targeted retrieval;
- immutable evidence provenance;
- deterministic hard gates;
- structured assessment;
- evidence-derived confidence;
- contradiction handling;
- human approval and audit.

The purpose is to show which architectural changes actually improve behavior.

## Evaluation dimensions

### 1. Safety and trust

- unsupported assertion rate;
- evidence/citation correctness;
- appropriate uncertainty;
- deterministic-rule compliance.

### 2. Detection

- critical-risk recall;
- contradiction recall;
- dependency and resource-conflict detection.

### 3. Judgment

- RAG agreement;
- forecast direction;
- confidence appropriateness;
- escalation level.

### 4. Decision quality

- intervention ranking;
- portfolio tradeoff quality;
- recognition of downstream consequences.

## Severity weighting

| Failure | Weight |
|---|---:|
| Missed critical risk or blocker | 5x |
| Unsupported high-confidence assertion | 5x |
| Incorrect RED/GREEN hard-gate judgment | 4x |
| Missed material contradiction | 4x |
| Incorrect evidence citation | 4x |
| Harmful portfolio intervention | 4x |
| Failure to say insufficient evidence | 3x |
| Incorrect forecast direction | 3x |
| Incorrect prioritization | 2x |
| Extra low-severity alert | 1x |

## Catastrophic release gate

A high aggregate score cannot compensate for a catastrophic trust failure.

V2 fails the release gate if it:

- fabricates material evidence;
- produces High-confidence GREEN despite a known mandatory blocker;
- misses a planted launch-critical risk that is clearly represented in the available evidence;
- recommends a consequential action without exposing evidence and tradeoffs.

## Minimum V2 demonstration

The prototype should detect at least four of five planted portfolio risks and demonstrate:

- evidence citations;
- contradiction handling;
- forecast RAG distinct from official RAG;
- confidence reduction under stale or conflicting evidence;
- recovery-plan credibility assessment;
- a cross-project resource/dependency conflict;
- a portfolio intervention with downstream consequences;
- Monday actions;
- Friday status;
- PM override;
- audit history;
- a proposed learning that does not silently alter global behavior.
