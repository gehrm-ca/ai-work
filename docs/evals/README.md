# Evaluation evidence

`v2-final-eval.json` is the unedited report of the final V2 benchmark: the weak
baseline and Program OS, run on the same 16 locked cases with the same model.

- Run: GitHub Actions run 43665330982, timestamp `2026-11-15T01:55:47Z`
- Model `gpt-6.1-sol`, OpenAI Agents SDK `0.24.0`, Program OS `0.2.0`, dataset `atlas-v2-001`
- Evaluated implementation commit: `0c84f439712a45eedb484d44f80682318138d9e0`

For each path, `paths.<name>` holds the weighted penalty, the failure counts by
dimension, and `cases`: every case's question, the model output and the failures
the scorer recorded. The summary and its caveats are in
[V2 evaluation results](../V2_EVALUATION_RESULTS.md).

The file was copied from that run's `v2-final-eval` artifact by a one-off workflow
and has not been edited.
