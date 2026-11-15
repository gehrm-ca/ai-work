# V2.1 external-validation plan

## Objective

V2.1 moves Program OS from a synthetic evaluated prototype to a product with evidence of external validity.

V2 proved the architecture on the Atlas benchmark. V2.1 tests four different questions:

1. Can the evidence model survive a real system of record?
2. Does the product help an experienced PM on real work?
3. Can a reviewer experience the product without local setup?
4. Are the production trust boundaries coherent enough for enterprise adoption?

The V2.1 tracking issue is [#21](https://github.com/gehrm-ca/ai-work/issues/21).

## Workstream 1 — live read-only ingestion

Tracking: [#17](https://github.com/gehrm-ca/ai-work/issues/17)

Start with one read-only source path.

The connector is successful only if it preserves provenance, timestamps, permissions, and partial-failure state. The milestone does not require production OAuth UX or write-back.

A live connector must not silently turn missing or inaccessible records into absence of risk.

## Workstream 2 — design-partner pilot

Tracking: [#18](https://github.com/gehrm-ca/ai-work/issues/18)

Run the weekly Program OS loop on one real program or portfolio.

Use [the design-partner pilot protocol](DESIGN_PARTNER_PILOT.md).

The output is not a testimonial exercise. It is a go/no-go product evaluation with explicit trust failures, false alerts, accepted/rejected recommendations, and outcome evidence.

## Workstream 3 — hosted deterministic demo

Tracking: [#19](https://github.com/gehrm-ca/ai-work/issues/19)

Publish the Atlas demo without exposing a model key.

The hosted path should demonstrate:

- official versus forecast RAG;
- Monday intervention queue;
- evidence IDs;
- portfolio tradeoff;
- Friday status;
- trust signals.

Live model calls should remain disabled until a separate secured deployment boundary exists.

## Workstream 4 — production trust boundaries

Tracking: [#20](https://github.com/gehrm-ca/ai-work/issues/20)

Document and then implement the minimum architecture needed for:

- tenant isolation;
- identity and RBAC;
- source-permission propagation;
- secret management;
- evidence retention/deletion;
- audit integrity;
- model-provider data boundaries;
- administrator approval of global AI behavior changes.

## Release gates

V2.1 is not complete until:

- one live or sandbox source is ingested with preserved provenance;
- one real-program pilot is completed;
- the public deterministic demo is available;
- production trust boundaries are documented;
- external failures are added to the eval corpus;
- zero consequential autonomous writes are introduced;
- the README distinguishes synthetic benchmark evidence from external-validation evidence.

## Anti-goals

Do not add the following merely because they make the architecture look more sophisticated:

- multi-agent orchestration;
- generic work-management features;
- autonomous status changes;
- autonomous risk-register mutation;
- broad integration count;
- vector retrieval for its own sake;
- fine-tuning.

Each requires a measured failure that the simpler architecture cannot solve adequately.

## Evidence hierarchy for V2.1 decisions

When deciding what to build next, weight evidence in this order:

1. catastrophic trust failure;
2. missed material risk;
3. bad portfolio intervention;
4. repeated PM rejection/modify pattern;
5. connector reliability or permission failure;
6. false-alert burden;
7. workflow friction;
8. latency/cost;
9. feature requests without observed failure evidence.

This keeps the roadmap driven by decision quality rather than feature volume.
