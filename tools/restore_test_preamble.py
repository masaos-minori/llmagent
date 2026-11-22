#!/usr/bin/env python3
"""restore_test_preamble.py — Put back the top-level definitions a bulk run deleted.

`merge_test_config_fixture_keys.py` once treated the module docstring as part of the import block,
so a run scanned past the docstring and deleted what it found there: the imports and the
module-level definitions after it (`def _msgs()`, `_SCHEMA_SQL`). A test that uses one of them now
reports an undefined name, so those are the lines this tool puts back.

For each given file, compare it with `git show HEAD:<path>`: for every top-level statement whose
source is absent from the current file, insert it after the current file's import block in HEAD's
order. Nothing the current file has is moved or removed, so a docstring the task reworded and the
lines it rewrote keep their place; a file with nothing missing is left alone. Run
`ruff check --fix` afterwards to drop any import that turns out to be unused and to restore the
import order. `--dry-run` prints the changed files.
"""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from pathlib import Path

import merge_test_config_fixture_keys as merge_tool

ROOT = Path(__file__).resolve().parent.parent


def head_text(path: Path) -> str:
    return subprocess.run(
        ["git", "show", f"HEAD:{path.relative_to(ROOT).as_posix()}"],
        capture_output=True,
        text=True,
        check=True,
    ).stdout


def missing_statements(text: str, original: str) -> list[str]:
    """Top-level statements in HEAD whose source is absent from the current file, in HEAD order."""
    tree = ast.parse(original)
    out: list[str] = []
    for node in tree.body:
        segment = ast.get_source_segment(original, node)
        if segment and segment not in text:
            out.append(segment)
    return out


def restore(text: str, original: str) -> tuple[str, int]:
    missing = missing_statements(text, original)
    if not missing:
        return text, 0
    anchor = merge_tool._import_block_end(text.splitlines(keepends=True))
    out = text.splitlines(keepends=True)[: anchor + 1]
    for segment in missing:
        out.append(f"\n{segment}\n")
    return "".join(out) + "".join(text.splitlines(keepends=True)[anchor + 1 :]), 1


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
            result, changed = restore(text, head_text(path))
        except (SyntaxError, ValueError) as exc:
            print(f"{path.relative_to(ROOT)}: skipped ({exc})", file=sys.stderr)
            continue
        if not changed:
            print(f"{path.relative_to(ROOT)}: nothing missing")
            continue
        if not args.dry_run:
            path.write_text(result, encoding="utf-8")
        print(
            f"{path.relative_to(ROOT)}: {changed} statement(s) inserted",
            file=sys.stderr,
        )
        total += changed
    return 0 if total else 1


if __name__ == "__main__":
    sys.exit(main())
