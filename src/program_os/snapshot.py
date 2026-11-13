"""Build an inspectable deterministic portfolio snapshot for the demo."""
from __future__ import annotations

from pathlib import Path

from .evidence import load_evidence_dir
from .recommendation import recommend_resource_tradeoff
from .signals import detect_signals


def build_atlas_snapshot(data_dir: Path) -> dict:
    evidence = load_evidence_dir(data_dir)
    signals = detect_signals(evidence)
    recommendation = recommend_resource_tradeoff(signals, evidence)
    return {
        "evidence_count": len(evidence),
        "signals": [
            {
                "kind": item.kind,
                "project_id": item.project_id,
                "severity": item.severity,
                "summary": item.summary,
                "evidence_ids": list(item.evidence_ids),
            }
            for item in signals
        ],
        "recommendation": (
            recommendation.model_dump(mode="json") if recommendation else None
        ),
    }
