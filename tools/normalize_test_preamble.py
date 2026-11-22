#!/usr/bin/env python3
"""normalize_test_preamble.py — Rebuild a test file's top from HEAD's docstring and import block.

`restore_test_preamble.py` inserts HEAD's top-level statements after the import block, so a file whose
docstring or import block is no longer at the top keeps them where they are, and an import list whose
contents were removed as duplicates leaves an empty paren. For each given test file, rebuild the region
before the first top-level def, class, or decorator as: the file's own module docstring, HEAD's import
block, then the lines the current file added there (its fixtures and constants) in the current order.
Nothing after the first top-level statement is changed. A file whose top is already in that shape is
left alone. Run `ruff check --fix` afterwards for the import order. `--dry-run` prints the changed files.
"""

from __future__ import annotations

import argparse
import re
import subprocess
import sys
from pathlib import Path

import merge_test_config_fixture_keys as merge_tool

ROOT = Path(__file__).resolve().parent.parent
FIRST_STATEMENT = re.compile(r"^(def |class |@)")


def head_text(path: Path) -> str:
    return subprocess.run(
        ["git", "show", f"HEAD:{path.relative_to(ROOT).as_posix()}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def normalize(text: str, original: str) -> tuple[str, int]:
    lines = text.splitlines(keepends=True)
    split = next(
        (idx for idx, line in enumerate(lines) if FIRST_STATEMENT.match(line)),
        len(lines),
    )
    head_lines = original.splitlines(keepends=True)
    head_doc_end = merge_tool._docstring_end(head_lines)
    if head_doc_end < 0:
        return text, 0
    head_imports = head_lines[
        head_doc_end + 1 : merge_tool._import_block_end(head_lines) + 1
    ]
    head_names = {line.strip() for line in head_imports if line.strip()}

    doc_end = merge_tool._docstring_end(lines)
    if doc_end < 0:
        doc = head_lines[: head_doc_end + 1]
        doc_end = -1
    else:
        doc = lines[: doc_end + 1]
    added = [
        line.rstrip("\n")
        for line in lines[doc_end + 1 : split]
        if line.strip() and line.strip() not in head_names
    ]

    out = (
        doc
        + ["\n"]
        + head_imports
        + [f"\n{line}\n" for line in added]
        + ["\n"]
        + lines[split:]
    )
    return "".join(out), 1


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--files", nargs="+", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    total = 0
    for name in args.files:
        path = Path(name) if Path(name).is_absolute() else ROOT / name
        text = path.read_text(encoding="utf-8")
        try:
            result, changed = normalize(text, head_text(path))
        except (SyntaxError, ValueError) as exc:
            print(f"{path.relative_to(ROOT)}: skipped ({exc})", file=sys.stderr)
            continue
        if result == text:
            print(f"{path.relative_to(ROOT)}: top already normal")
            continue
        if not args.dry_run:
            path.write_text(result, encoding="utf-8")
        print(f"{path.relative_to(ROOT)}: top rebuilt", file=sys.stderr)
        total += changed
    return 0 if total else 1


if __name__ == "__main__":
    sys.exit(main())
