# Tests

V2 includes executable unit, integration-contract and evaluation tests.

Run the local test suite from the repository root:

~~~bash
python -m pip install -e ".[dev]"
python -m pytest -q
~~~

CI also builds the Next.js frontend and both Docker images.

## Current coverage areas

The unit suite covers:

- source-adapter contracts and read-only JSON ingestion;
- Jira pagination, permission and partial-retrieval behavior;
- protected API feature gating, bearer authentication and demo rate limiting;
- immutable evidence loading;
- deterministic controls and confidence logic;
- grounding and citation validation;
- retrieval and signal detection;
- priority and recommendation behavior;
- audit/override semantics;
- static showcase generation;
- evaluation scoring and live-eval harness behavior.

The locked golden cases live under tests/evals/gold/. They were created before final V2 tuning so architecture changes can be compared against a stable target.

See [Evaluation strategy](../docs/EVAL_STRATEGY.md), [Run evaluations](../docs/RUN_EVALS.md), and [V2 evaluation results](../docs/V2_EVALUATION_RESULTS.md).
