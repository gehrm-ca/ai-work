"""Lightweight credential-pattern check for tracked repository files.

Use --history on a full local clone to inspect historic patches. This supplements,
but does not replace, GitHub secret-scanning or a dedicated secret scanner.
Do not print matching secret contents to logs.
"""
from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path

PATTERNS = (
    ("Stripe secret", re.compile(r"sk_(?:live|test)_[A-Za-z0-9]{12,}")),
    ("OpenAI credential", re.compile(r"sk-(?:proj-|svcacct-|admin-)?[A-Za-z0-9_-]{24,}")),
    ("GitHub token", re.compile(r"(?:ghp|gho|ghu|ghs|ghr)_[A-Za-z0-9]{25,}")),
    ("AWS key", re.compile(r"AKIA[0-9A-Z]{16}")),
    ("Private key", re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----")),
    ("Slack token", re.compile(r"xox[baprs]-[A-Za-z0-9-]{15,}")),
)
SKIP_SUFFIXES = (".png", ".jpg", ".jpeg", ".gif", ".pdf", ".ico", ".lock")


def matches(content: str) -> list[str]:
    return [name for name, pattern in PATTERNS if pattern.search(content)]


def tracked_scan() -> list[str]:
    result = subprocess.run(["git", "ls-files", "-z"], capture_output=True, check=True)
    findings: list[str] = []
    for filename in result.stdout.split(b"\x00"):
        if not filename:
            continue
        path = Path(filename.decode("utf-8", "surrogateescape"))
        if path.suffix.lower() in SKIP_SUFFIXES or not path.is_file():
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeError, OSError):
            continue
        for name in matches(content):
            findings.append(f"{path}: {name}")
    return findings


def history_scan() -> list[str]:
    result = subprocess.run(
        ["git", "log", "--all", "-p", "--no-ext-diff", "--no-textconv"],
        capture_output=True, check=True,
    )
    content = result.stdout.decode("utf-8", errors="replace")
    return [f"Git history: {name}" for name in matches(content)]


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--history", action="store_true", help="Also scan all available Git history")
    args = parser.parse_args()
    findings = tracked_scan()
    if args.history:
        findings.extend(history_scan())
    if findings:
        for finding in sorted(set(findings)):
            print(f"Potential secret: {finding}")
        raise SystemExit(1)
    print("No credentials matching the configured high-confidence patterns were found.")


if __name__ == "__main__":
    main()
