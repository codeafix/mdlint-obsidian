"""CLI entry point for obsidian-lint."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import validate
from .models import Severity


def _format_text(file_path: Path, errors: list) -> list[str]:
    lines = []
    for e in errors:
        level = "ERROR" if e.severity == Severity.ERROR else "WARNING"
        lines.append(f"{file_path}:{e.line}: [{level}] {e.rule}: {e.message}")
    return lines


def _format_json(file_path: Path, errors: list) -> list[dict]:
    return [
        {
            "file": str(file_path),
            "line": e.line,
            "rule": e.rule,
            "severity": e.severity.value,
            "message": e.message,
        }
        for e in errors
    ]


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="obsidian-lint",
        description="Lint Obsidian Flavored Markdown files.",
    )
    parser.add_argument("path", help="File or directory to lint")
    parser.add_argument(
        "--vault",
        metavar="VAULT_PATH",
        default=None,
        help="Vault root directory (enables broken-link checking)",
    )
    parser.add_argument(
        "--severity",
        choices=["error", "warning"],
        default=None,
        help="Only report issues at this severity or above (error > warning)",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json"],
        default="text",
        help="Output format (default: text)",
    )

    args = parser.parse_args(argv)
    target = Path(args.path)

    if target.is_dir():
        files = sorted(target.rglob("*.md"))
    elif target.is_file():
        files = [target]
    else:
        print(
            f"obsidian-lint: {target}: no such file or directory",
            file=sys.stderr,
        )
        sys.exit(2)

    has_errors = False
    json_output: list[dict] = []

    for file in files:
        try:
            content = file.read_text(encoding="utf-8")
        except OSError as exc:
            print(f"obsidian-lint: {file}: {exc}", file=sys.stderr)
            continue

        errors = validate(content, vault_path=args.vault)

        # Severity filter: "error" means suppress warnings
        if args.severity == "error":
            errors = [e for e in errors if e.severity == Severity.ERROR]

        if errors:
            if any(e.severity == Severity.ERROR for e in errors):
                has_errors = True

            if args.format == "json":
                json_output.extend(_format_json(file, errors))
            else:
                for line in _format_text(file, errors):
                    print(line)

    if args.format == "json":
        print(json.dumps(json_output, indent=2))

    sys.exit(1 if has_errors else 0)


if __name__ == "__main__":
    main()
