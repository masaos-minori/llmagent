#!/usr/bin/env python3
"""tools/fix_mock_context_manager.py

Adds the context-manager self-return to `RepositoryState` mocks under `tests/`.

The code under test holds a `RepositoryState` through its context-manager form
(`with RepositoryState.snapshot(...) as state:`), so a mock injected as the return value of
`RepositoryState.snapshot()` must return itself from `__enter__`; otherwise the `with` target
is a fresh mock and the attributes configured on the original mock are lost.

For every `tests/**/*.py` line that assigns a `MagicMock` used as the `RepositoryState`
double — either `MagicMock(spec=RepositoryState)` or a plain `MagicMock()` whose variable is
the `return_value` of a `patch.object(RepositoryState, "snapshot", return_value=...)` — the tool
inserts `<var>.__enter__.return_value = <var>` immediately after it (no-op when the line
is already present). A short comment is added at the first insertion in each file.

Usage:
    python tools/fix_mock_context_manager.py --dry-run tests/mcp_servers/git
    python tools/fix_mock_context_manager.py --apply tests/mcp_servers/git
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._atomic_write import atomic_write_text

ASSIGN_RE = re.compile(r"^(\s*)(\w+) = MagicMock\((?:spec=RepositoryState)?\)\s*$")
SNAPSHOT_PATCH_RE = re.compile(
    r'patch\.object\(RepositoryState, "snapshot", return_value=(\w+)\)'
)
COMMENT = (
    "# RepositoryState is used through its context-manager form in the code under test."
)


def fix_text(text: str) -> tuple[str, int]:
    """Return the rewritten text and the number of insertions made."""
    patched = set(SNAPSHOT_PATCH_RE.findall(text))
    lines = text.splitlines(keepends=True)
    out: list[str] = []
    inserted = 0
    commented = False
    for index, line in enumerate(lines):
        out.append(line)
        match = ASSIGN_RE.match(line.rstrip("\n"))
        if match is None:
            continue
        indent, name = match.group(1), match.group(2)
        if name not in patched and "spec=RepositoryState" not in line:
            continue
        expected = f"{name}.__enter__.return_value = {name}"
        if any(
            stripped.strip() == expected for stripped in lines[index + 1 : index + 3]
        ):
            continue
        if not commented:
            out.append(f"{indent}{COMMENT}\n")
            commented = True
        out.append(f"{indent}{name}.__enter__.return_value = {name}\n")
        inserted += 1
    return "".join(out), inserted


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[2])
    parser.add_argument("paths", nargs="+", help="test files or directories to scan")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--dry-run", action="store_true", help="report without writing")
    mode.add_argument("--apply", action="store_true", help="write the insertions")
    args = parser.parse_args(argv)

    files: list[Path] = []
    for raw in args.paths:
        path = Path(raw)
        if path.is_dir():
            files.extend(sorted(path.glob("**/*.py")))
        elif path.is_file():
            files.append(path)
        else:
            print(f"not found: {path}", file=sys.stderr)
            return 2

    changed = 0
    for path in files:
        text = path.read_text(encoding="utf-8")
        new_text, count = fix_text(text)
        if count == 0:
            continue
        changed += count
        print(f"{path}: {count} insertion(s)")
        if args.apply:
            atomic_write_text(path, new_text)

    if changed == 0:
        print("no mock context-manager lines to add")
    elif args.dry_run:
        print(f"{changed} insertion(s) pending (--apply to write)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
