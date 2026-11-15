"""Static showcase export for the public GitHub Pages demo."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from .demo import build_demo_payload


def export_showcase(
    output: Path,
    *,
    data_dir: Path = Path("examples/atlas/data"),
) -> dict:
    payload = build_demo_payload(data_dir)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, indent=2, default=str),
        encoding="utf-8",
    )
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export deterministic Atlas showcase data."
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("_site/atlas-demo.json"),
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=Path("examples/atlas/data"),
    )
    args = parser.parse_args()
    payload = export_showcase(args.output, data_dir=args.data_dir)
    print(
        json.dumps(
            {
                "output": str(args.output),
                "evidence_count": payload["evidence_count"],
                "monday_actions": len(payload["monday_actions"]),
                "signals": len(payload["signals"]),
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
