"""Local helper for design-partner pilot records.

Pilot records can contain sensitive content. Store them under var/pilots/, which
is ignored by Git. This tool never uploads data.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from program_os.pilot import PilotRecord, new_pilot_record


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

    ready = sub.add_parser(
        "check-ready",
        help="Require baseline and evidence snapshot before Program OS analysis.",
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
                },
                indent=2,
            )
        )
        return

    record = load(args.path)

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
        if not record.ready_for_analysis:
            raise SystemExit(
                "Pilot is not ready: record the human baseline and freeze an "
                "evidence snapshot before Program OS analysis."
            )
        print(json.dumps({"ready_for_analysis": True}, indent=2))
        return

    if args.command == "summary":
        print(json.dumps(record.aggregate_summary(), indent=2))
        return


if __name__ == "__main__":
    main()
