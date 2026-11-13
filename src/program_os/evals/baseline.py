"""Intentionally weak V2 baseline.

This module is not the target architecture. It exists so Program OS can be
evaluated against a naive "stuff the portfolio into one prompt" approach.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

ATLAS_FILES = (
    "jira_issues.json",
    "risks.json",
    "project_pages.json",
    "meeting_notes.json",
    "quality_reports.json",
    "decisions.json",
    "retrospectives.json",
    "budget_snapshots.json",
    "resource_snapshots.json",
    "status_reports.json",
    "dependencies.json",
    "milestones.json",
)

SYSTEM_PROMPT = """You are a program-management assistant.
Review the supplied portfolio context and return a concise launch-readiness
assessment with RAG, risks, confidence, and recommended actions.
Use only the supplied context. If information is missing, say so.
"""


def load_raw_context(data_dir: Path, files: Iterable[str] = ATLAS_FILES) -> str:
    """Load all evidence as raw JSON text with no targeted retrieval."""
    chunks: list[str] = []
    for filename in files:
        path = data_dir / filename
        payload = json.loads(path.read_text(encoding="utf-8"))
        chunks.append(f"## {filename}\n{json.dumps(payload, indent=2)}")
    return "\n\n".join(chunks)


def build_baseline_prompt(question: str, raw_context: str) -> str:
    """Build one broad prompt. Deliberately provides no rule/retrieval scaffold."""
    return f"{SYSTEM_PROMPT}\n\nPORTFOLIO CONTEXT\n{raw_context}\n\nQUESTION\n{question}\n"


def expected_failure_modes() -> tuple[str, ...]:
    return (
        "context dilution",
        "stale evidence overweighting",
        "weak contradiction handling",
        "unsupported certainty",
        "inconsistent hard-gate behavior",
    )
