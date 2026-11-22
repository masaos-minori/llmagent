#!/usr/bin/env python3
"""merge_test_config_fixture_keys.py — Add a shared fixture merge to a test config dict.

Test fixtures that pass a mapping to `build_agent_config()` must supply the keys the typed
builders read from it. For Plan agentcfg004 that is the mirrored DB path block
(`SHIPPED_DB_PATH_KEYS` in `tests/agent/_config_test_defaults.py`), because `build_db_config()`
now takes the mapping from its caller instead of reading `config/agent.toml`.

For each file given:
  - insert `<indent>**<merge>,` after the dict entry named by `--anchor`, keeping the
    fixture's indentation
  - make the fixture reachable: add it to the file's existing top-level import of
    `<import-module>`, or add a new import after the top-level import block

A file with no fixture dict is left alone: the import is only added where the merge entry is
used.

The comment names why the merge is there, so the fixture is not read as an unrelated
spread. The run is idempotent: an existing merge entry and an existing import are left
alone, and an import placed inside a function body or inside a parenthesized import list by
an earlier pass is moved to the top-level import block. `--dry-run` prints the result and
changes nothing.
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REASON = (
    "build_agent_config() resolves the typed DB configuration from the mapping, so the "
    "fixture supplies the mirrored path keys."
)


def _docstring_end(lines: list[str]) -> int:
    """Index of the line closing the module docstring, or -1 when there is none."""
    if not lines or not lines[0].strip().startswith('"""'):
        return -1
    if lines[0].strip() != '"""' and lines[0].strip().endswith('"""'):
        return 0
    idx = 1
    while idx < len(lines) and lines[idx].strip() != '"""':
        idx += 1
    return idx


def _import_block_end(lines: list[str]) -> int:
    """Index of the last line of the top-level import block (0-based).

    The module docstring is skipped; the scan stops at the first top-level statement that
    is not an import, so an import the earlier pass placed inside a function body or inside
    a parenthesized import list is not mistaken for the end of the block.
    """
    last = 0
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        stripped = line.strip()
        if not stripped:
            idx += 1
            continue
        if stripped.startswith('"""'):
            # A docstring that opens and closes on the same line is one line; the opening
            # quote alone is not the end of the block, so the scan continues past the
            # closing quote instead of treating it as the start of another docstring.
            if stripped != '"""' and stripped.endswith('"""'):
                idx += 1
                continue
            idx += 1
            while idx < len(lines) and lines[idx].strip() != '"""':
                idx += 1
            idx += 1
            continue
        if line.startswith(("import ", "from ")):
            depth = line.count("(") - line.count(")")
            while depth > 0 and idx + 1 < len(lines):
                idx += 1
                depth += lines[idx].count("(") - lines[idx].count(")")
            last = idx
            idx += 1
            continue
        break
    return last


def merge(text: str, anchor: str, merge_name: str, module: str) -> tuple[str, int]:
    """Insert the spread after the anchor entry and make the fixture import top level."""
    lines = text.splitlines(keepends=True)
    block_end = _import_block_end(lines)
    doc_end = _docstring_end(lines)

    # An import this tool wrote earlier that ended up inside the module docstring, inside a
    # function body, or inside a parenthesized import list is taken back out of there.
    targets = (f"from {module} import {merge_name}", f"{merge_name},")
    misplaced = [
        idx
        for idx, line in enumerate(lines)
        if line.strip() in targets
        and ((doc_end >= 0 and idx < doc_end) or idx > block_end)
    ]

    out: list[str] = []
    changed = 0
    already_merged = any(
        line.strip() == f"**{merge_name},"
        for line in lines
        if not line.strip().startswith("#")
    )
    entry = re.compile(rf'^\s*"{re.escape(anchor)}": ')
    for idx, line in enumerate(lines):
        if idx in misplaced:
            continue
        out.append(line)
        if already_merged or not entry.match(line):
            continue
        indent = line[: len(line) - len(line.lstrip())]
        out.append(f"{indent}# {REASON}\n")
        out.append(f"{indent}**{merge_name},\n")
        changed += 1

    if not already_merged and not changed:
        # A file with no fixture dict does not need the import: nothing here uses the fixture.
        return "".join(out), len(misplaced)

    existing = [
        idx for idx, line in enumerate(out) if line.startswith(f"from {module} import")
    ]
    if existing:
        target = out[existing[0]]
        if target.rstrip().endswith("("):
            # Parenthesized block: names are sorted, so insert at the sorted position.
            end = existing[0] + 1
            while end < len(out) and out[end].strip() != ")":
                end += 1
            names = [
                out[idx].strip().rstrip(",") for idx in range(existing[0] + 1, end)
            ]
            if merge_name not in names:
                insert_at = next(
                    (
                        idx
                        for idx in range(existing[0] + 1, end)
                        if out[idx].strip().rstrip(",") > merge_name
                    ),
                    end,
                )
                out.insert(insert_at, f"    {merge_name},\n")
                changed += 1
        else:
            names = target.rstrip().removeprefix(f"from {module} import ").split(", ")
            if merge_name not in names:
                names.append(merge_name)
                out[existing[0]] = f"from {module} import {', '.join(sorted(names))}\n"
                changed += 1
    else:
        out.insert(block_end + 1, f"\nfrom {module} import {merge_name}\n")
        changed += 1

    return "".join(out), changed + len(misplaced)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument(
        "--anchor", required=True, help="dict key the fixture already has"
    )
    parser.add_argument(
        "--merge", required=True, help="fixture name to spread into the dict"
    )
    parser.add_argument("--import-module", required=True)
    parser.add_argument("--files", nargs="+", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    total = 0
    for name in args.files:
        path = Path(name) if Path(name).is_absolute() else ROOT / name
        text = path.read_text(encoding="utf-8")
        result, changed = merge(text, args.anchor, args.merge, args.import_module)
        total += changed
        if not changed:
            print(f"{path.relative_to(ROOT)}: no occurrence")
            continue
        if args.dry_run:
            print(result)
        else:
            path.write_text(result, encoding="utf-8")
        print(f"{path.relative_to(ROOT)}: {changed} change(s)", file=sys.stderr)
    if not total:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
