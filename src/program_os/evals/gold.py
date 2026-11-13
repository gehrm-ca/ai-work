"""Load the fixed gold set without exposing it to runtime prompts."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_gold_cases(path: Path) -> list[dict[str, Any]]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    return payload["cases"]


def evidence_ids_for_case(case: dict[str, Any]) -> set[str]:
    return set(case.get("evidence", []))


def must_not_assert(case: dict[str, Any]) -> tuple[str, ...]:
    return tuple(case.get("expected", {}).get("must_not_assert", []))
