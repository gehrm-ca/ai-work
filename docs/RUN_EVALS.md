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


## GitHub Actions release gate

The repository includes `.github/workflows/live-evals.yml` as a manual release gate.

The workflow requires:

- a repository Actions secret named `OPENAI_API_KEY`;
- an explicit model identifier supplied when the workflow is started.

The workflow:

1. installs the exact repository revision;
2. runs all 16 cases through the weak baseline;
3. runs the same 16 cases through Program OS;
4. writes `artifacts/eval-report.json`;
5. publishes headline results to the GitHub Actions job summary;
6. fails the workflow if Program OS has any catastrophic release-gate failure;
7. uploads the full JSON report as a workflow artifact.

The API key is consumed only as a GitHub Actions secret and is not written to the repository or evaluation report.
