# Tests

V1 contains the evaluation contract. V2 will add executable tests.

Planned structure:

~~~text
tests/
  unit/
    test_rag_rules.py
    test_confidence.py
    test_permissions.py
  evals/
    cases/
    test_golden_cases.py
    test_baseline.py
~~~

The golden evaluation set is created before model and retrieval optimization so architecture changes can be compared against a stable target.

See [docs/EVAL_STRATEGY.md](../docs/EVAL_STRATEGY.md).
