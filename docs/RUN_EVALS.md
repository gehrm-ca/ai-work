# Running V2 evaluations

Program OS uses two evaluation modes.

## Offline smoke

This runs in CI and does not call a model.

```bash
python - <<'PY'
from pathlib import Path
from program_os.evals.smoke import run_signal_smoke
print(run_signal_smoke(Path("examples/atlas/data")))
PY
```

It verifies that the deterministic Atlas signal layer still detects the planted
portfolio signals. It is not the baseline comparison and must not be presented as
AI-quality evidence.

## Live baseline comparison

The final V2 release gate requires a live run.

Set an OpenAI API key and choose the exact model identifier you intend to record:

```bash
export OPENAI_API_KEY=...
python -m program_os.evals.live \
  --model YOUR_MODEL_ID \
  --output artifacts/eval-report.json
```

The runner makes two passes over the same 16 locked cases:

1. **Weak baseline** — all raw Atlas evidence in one prompt, no targeted retrieval,
   no deterministic hard gates, and no application-level provenance validation.
2. **Program OS** — targeted retrieval, structured single-agent interpretation,
   application-level citation validation, evidence-derived confidence, and
   deterministic hard gates.

Gold expectations and required citations are loaded only after each model output is
generated. They are not supplied to either prompt.

The report records:

- timestamp;
- exact model identifier;
- Agents SDK version;
- Program OS version;
- per-case output;
- per-case failures;
- weighted penalty;
- catastrophic failures;
- failures by Safety/Trust, Detection, Judgment, and Decision Quality.

A final V2 release requires zero catastrophic Program OS failures.
