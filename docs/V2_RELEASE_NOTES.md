# V2 release notes

**Release:** Program OS V2 — evaluated prototype  
**Released:** November 14, 2026  
**System version:** `0.2.0`

## What shipped

V2 is the first working end-to-end Program OS vertical slice.

It includes:

- the fictional Atlas five-workstream launch portfolio;
- 48 timestamped, provenance-ranked evidence artifacts;
- immutable evidence loading;
- a canonical program model;
- deterministic hard RAG gates;
- evidence-derived confidence;
- deterministic signal detection;
- targeted retrieval plus explicit evidence joins;
- one structured AI analyst;
- citation validation;
- official versus forecast RAG;
- Monday intervention prioritization;
- portfolio resource tradeoff recommendations;
- Friday evidence-backed status;
- PM override;
- append-only audit;
- governed learning proposals;
- FastAPI endpoints;
- a Next.js demo UI;
- a 16-case live evaluation harness;
- a weak-baseline comparison;
- GitHub CI for Python and the production web build.

## Measured evaluation

The final V2 run used the same `gpt-6.1-sol` model and the same 16 locked cases for both paths.

| Metric | Weak baseline | Program OS |
|---|---:|---:|
| Severity-weighted failure penalty | 60 | **3** |
| Clean cases | 4/16 | **15/16** |
| Safety/Trust failures | 2 | **0** |
| Detection failures | 3 | **0** |
| Decision Quality failures | 6 | **0** |
| Judgment failures | 9 | **1** |
| Catastrophic failures | 0 | **0** |

The remaining failure is E14: Program OS returns AMBER rather than GREEN after a formally resolved scope reduction.

See [V2 evaluation results](V2_EVALUATION_RESULTS.md) for methodology and integrity notes.

## Deliberately not in V2

- production Jira/Confluence OAuth;
- enterprise SSO and full RBAC;
- PostgreSQL/pgvector persistence;
- production observability and SLOs;
- multi-agent orchestration;
- autonomous consequential writes;
- enterprise deployment or compliance certification.

## Why single-agent first

Multi-agent orchestration is not a product goal by itself.

V2 uses one structured analyst because the benchmark did not establish a need for multiple runtime agents. Additional agents should be introduced only if a controlled evaluation demonstrates better quality, reliability, latency, cost, or maintainability.

## Next

The next product phase should focus on external validity rather than more synthetic benchmark tuning:

- run Program OS against realistic customer/design-partner artifacts;
- connect one live system of record;
- measure time-to-detection and intervention usefulness;
- test portfolio-level recommendations with experienced program leaders;
- harden tenant isolation, authorization, and production observability.
