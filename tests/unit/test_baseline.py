from pathlib import Path

from program_os.evals.baseline import build_baseline_prompt, expected_failure_modes


def test_baseline_is_explicitly_naive():
    prompt = build_baseline_prompt("Can Atlas launch?", "raw evidence")
    assert "raw evidence" in prompt
    assert "Can Atlas launch?" in prompt
    assert "contradiction graph" not in prompt.lower()


def test_failure_modes_are_documented():
    assert "unsupported certainty" in expected_failure_modes()
