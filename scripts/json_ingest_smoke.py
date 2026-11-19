"""Validate a local read-only JSON export against the Program OS source contract."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from program_os.adapters import ReadOnlyJsonAdapter, normalize_batch
from program_os.readiness import assess_evidence_readiness


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Validate a local JSON export without printing source content."
    )
    parser.add_argument("path", type=Path, help="JSON object or array of source records.")
    parser.add_argument("--connector-id", default="json-export")
    parser.add_argument("--principal")
    parser.add_argument("--show-source-ids", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    adapter = ReadOnlyJsonAdapter(
        args.path,
        connector_id=args.connector_id,
        principal=args.principal,
    )
    batch = adapter.fetch()
    evidence = normalize_batch(batch)
    readiness = assess_evidence_readiness(batch)

    summary: dict[str, object] = {
        "connector_id": batch.connector_id,
        "records": len(evidence),
        "complete": batch.complete,
        "failure_kinds": [failure.kind.value for failure in batch.failures],
        "evidence_readiness": readiness.model_dump(mode="json"),
    }
    if args.show_source_ids:
        summary["sample_evidence_ids"] = [item.evidence_id for item in evidence[:10]]

    print(json.dumps(summary, indent=2))
    if not batch.complete:
        raise SystemExit(2)


if __name__ == "__main__":
    main()
