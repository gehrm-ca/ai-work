"""Local helper for design-partner pilot records.

Pilot records can contain sensitive content. Store them under var/pilots/, which
is ignored by Git. This tool never uploads data.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from program_os.pilot import PilotRecord, new_pilot_record
from program_os.readiness import EvidenceReadinessReport


def load(path: Path) -> PilotRecord:
    return PilotRecord.model_validate_json(path.read_text(encoding="utf-8"))


def save(path: Path, record: PilotRecord) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        record.model_dump_json(indent=2),
        encoding="utf-8",
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="Manage local Program OS pilot records.")
    sub = parser.add_subparsers(dest="command", required=True)

    init = sub.add_parser("init", help="Create an empty local pilot record.")
    init.add_argument("--pilot-id", required=True)
    init.add_argument("--program-alias", required=True)
    init.add_argument(
        "--output",
        type=Path,
        default=Path("var/pilots/pilot.json"),
    )

    validate = sub.add_parser("validate", help="Validate a pilot record.")
    validate.add_argument("path", type=Path)

    attach = sub.add_parser(
        "attach-readiness",
        help="Attach a smoke-test evidence readiness result to the frozen snapshot.",
    )
    attach.add_argument("path", type=Path)
    attach.add_argument(
        "readiness_path",
        type=Path,
        help="JSON emitted by json_ingest_smoke.py/jira_ingest_smoke.py or a raw readiness report.",
    )

    ready = sub.add_parser(
        "check-ready",
        help="Require baseline, evidence snapshot, and pilot-candidate readiness before analysis.",
    )
    ready.add_argument("path", type=Path)

    summary = sub.add_parser(
        "summary",
        help="Print aggregate review counts without finding text or evidence IDs.",
    )
    summary.add_argument("path", type=Path)

    args = parser.parse_args()

    if args.command == "init":
        record = new_pilot_record(args.pilot_id, args.program_alias)
        save(args.output, record)
        print(
            json.dumps(
                {
                    "created": str(args.output),
                    "pilot_id": record.pilot_id,
                    "ready_for_analysis": record.ready_for_analysis,
                    "readiness_level": (
                        record.evidence_snapshot.readiness_level.value
                        if record.evidence_snapshot
                        and record.evidence_snapshot.readiness_level is not None
                        else None
                    ),
                },
                indent=2,
            )
        )
        return

    record = load(args.path)

    if args.command == "attach-readiness":
        if record.evidence_snapshot is None:
            raise SystemExit(
                "Pilot has no evidence_snapshot. Freeze the snapshot before attaching readiness."
            )
        try:
            raw = json.loads(args.readiness_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise SystemExit(f"Could not read readiness JSON: {exc}") from exc
        candidate = raw.get("evidence_readiness", raw) if isinstance(raw, dict) else raw
        try:
            readiness = EvidenceReadinessReport.model_validate(candidate)
        except Exception as exc:
            raise SystemExit("Readiness JSON does not match the Program OS readiness contract.") from exc

        record.evidence_snapshot = record.evidence_snapshot.model_copy(
            update={
                "readiness_level": readiness.readiness_level,
                "readiness_limitations": readiness.limitations,
            }
        )
        save(args.path, record)
        print(
            json.dumps(
                {
                    "pilot_id": record.pilot_id,
                    "readiness_level": readiness.readiness_level.value,
                    "limitation_count": len(readiness.limitations),
                    "ready_for_analysis": record.ready_for_analysis,
                },
                indent=2,
            )
        )
        return

    if args.command == "validate":
        print(
            json.dumps(
                {
                    "valid": True,
                    "pilot_id": record.pilot_id,
                    "ready_for_analysis": record.ready_for_analysis,
                },
                indent=2,
            )
        )
        return

    if args.command == "check-ready":
        if record.baseline is None:
            raise SystemExit(
                "Pilot is not ready: record the human baseline before Program OS analysis."
            )
        if record.evidence_snapshot is None:
            raise SystemExit(
                "Pilot is not ready: freeze an evidence snapshot before Program OS analysis."
            )
        if record.evidence_snapshot.readiness_level is None:
            raise SystemExit(
                "Pilot is not ready: attach an evidence readiness result before Program OS analysis."
            )
        if not record.ready_for_analysis:
            raise SystemExit(
                "Pilot is not ready: evidence readiness must be pilot_candidate for the "
                "full design-partner analysis."
            )
        print(
            json.dumps(
                {
                    "ready_for_analysis": True,
                    "readiness_level": record.evidence_snapshot.readiness_level.value,
                },
                indent=2,
            )
        )
        return

    if args.command == "summary":
        print(json.dumps(record.aggregate_summary(), indent=2))
        return


if __name__ == "__main__":
    main()
