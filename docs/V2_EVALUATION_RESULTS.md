# V2 Evaluation Results

**Release status:** Evaluated prototype  
**Benchmark run:** November 14, 2026 (run timestamp 2026-11-15T01:55:47.630889+00:00)  
**GitHub Actions run:** 43665330982  
**Evaluated implementation commit:** `0c84f439712a45eedb484d44f80682318138d9e0`

## Configuration

- Model: `gpt-6.1-sol`
- OpenAI Agents SDK: `0.24.0`
- Program OS system version: `0.2.0`
- Dataset: `atlas-v2-001`
- Golden cases: 16
- Same model used for weak baseline and Program OS paths
- Gold expectations were not included in either model prompt
- Catastrophic failures remained an independent release gate

## Final measured comparison

| Metric | Weak baseline | Program OS |
|---|---:|---:|
| Severity-weighted failure penalty | 60 | **3** |
| Cases with zero scored failures | 4/16 | **15/16** |
| Judgment failures | 9 | **1** |
| Detection failures | 3 | **0** |
| Decision Quality failures | 6 | **0** |
| Safety/Trust failures | 2 | **0** |
| Catastrophic failures | 0 | **0** |

The severity-weighted penalty fell by **95% relative to the weak baseline within this benchmark** (60 to 3). This is an evaluation result on the synthetic Atlas benchmark, not a claim of 95% improvement on real enterprise programs.

## What the architecture changed

The weak baseline receives the raw portfolio context in one broad prompt.

Program OS adds:

- deterministic evidence joins around known program-management signal classes;
- immutable evidence provenance;
- explicit official-versus-forecast RAG semantics;
- deterministic hard gates;
- evidence-derived confidence calibration;
- structured single-agent output;
- citation validation;
- deterministic signal augmentation for contradictions and known operational signals;
- RAG scope consistency between work-item, project, and portfolio levels.

The final benchmark indicates that these controls materially improved performance on the Atlas test set, especially for trust, detection, and decision-quality behaviors.

## Remaining scored failure

### E14 — Scope reduction after formal alignment

Expected: GREEN  
Observed: AMBER  
Failure: incorrect forecast direction

Scenario state says export filtering has been formally removed from launch scope, the baseline is updated, and stakeholders are aligned. Program OS remains conservative and returns AMBER.

This is retained as a known V2 limitation rather than modifying the gold case or continuing to tune against the benchmark. It is not a catastrophic trust failure.

## Evaluation integrity notes

The first measured run exposed real problems in retrieval, confidence calibration, scorer semantics, and RAG scope. Those failures were used as a defect backlog.

One gold expectation was refined during hardening: E07 represents an unverified mandatory approval where the product contract states that status **cannot be GREEN**. The original gold required exactly AMBER. It now accepts AMBER or RED because the locked product rule defines a ceiling, not an exact forecast state.

The scorer was also improved to handle equivalent program-management language and explicit negation. Because the scorer and the E07 expectation changed during hardening, early benchmark penalties such as 103/93 are **not directly comparable** with the final 60/3 result. The valid final comparison is baseline versus Program OS within the same final run.

No gold expectation was weakened to remove the remaining E14 failure.

## Release decision

V2 passes the release gate because:

- all 16 cases executed on both paths;
- Program OS had zero catastrophic failures;
- Program OS had zero Safety/Trust failures;
- Program OS had zero Detection failures;
- Program OS had zero Decision Quality failures;
- 15 of 16 Program OS cases had no scored failure;
- the remaining failure is disclosed.

V2 remains a portfolio and learning prototype. These results do not establish production reliability on real organizational data.
