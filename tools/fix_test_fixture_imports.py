#!/usr/bin/env python3
"""fix_test_fixture_imports.py — Add the fixture names a test file uses but does not import.

Run `ruff check --select F821` for the given test files; for every name that `tests/agent/_config_test_defaults.py`
defines, add it to the file's import of that module, or create the import after the file's
top-level import block when it has none. Names that are already imported are left alone, so the
run is idempotent.

The added block is placed as the file's own group; run `ruff check --fix` afterwards to bring it
into the repository's import order.
"""

from __future__ import annotations

import argparse
import ast
import subprocess
import sys
from pathlib import Path

import merge_test_config_fixture_keys as merge_tool

ROOT = Path(__file__).resolve().parent.parent
MODULE = "tests.agent._config_test_defaults"


def fixture_names() -> set[str]:
    tree = ast.parse(
        (ROOT / "tests/agent/_config_test_defaults.py").read_text(encoding="utf-8")
    )
    names: set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.Assign) and isinstance(node.targets[0], ast.Name):
            names.add(node.targets[0].id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.add(node.target.id)
    return names


def ruff_f821(path: Path) -> list[str]:
    out = subprocess.run(
        ["ruff", "check", "--select", "F821", "--output-format", "concise", str(path)],
        capture_output=True,
        text=True,
    ).stdout
    names: list[str] = []
    for line in out.splitlines():
        if "Undefined name" in line:
            name = line.rsplit("`", 2)[-2]
            if name and name not in names:
                names.append(name)
    return names


def add_names(text: str, names: list[str]) -> tuple[str, int]:
    lines = text.splitlines(keepends=True)
    block_end = merge_tool._import_block_end(lines)
    out = lines[: block_end + 1]

    existing = next(
        (
            idx
            for idx, line in enumerate(out)
            if line.startswith(f"from {MODULE} import")
        ),
        None,
    )
    if existing is None:
        out.append(f"\nfrom {MODULE} import {', '.join(sorted(names))}\n")
        return "".join(out) + "".join(lines[block_end + 1 :]), len(names)

    if out[existing].rstrip().endswith("("):
        end = existing + 1
        while end < len(out) and out[end].strip() != ")":
            end += 1
        present = [out[idx].strip().rstrip(",") for idx in range(existing + 1, end)]
        wanted = sorted(set(present) | set(names))
        body = [f"    {name},\n" for name in wanted]
        out[existing + 1 : end] = body
    else:
        present = (
            out[existing].rstrip().removeprefix(f"from {MODULE} import ").split(", ")
        )
        wanted = sorted(set(present) | set(names))
        out[existing] = f"from {MODULE} import {', '.join(wanted)}\n"

    return "".join(out) + "".join(lines[block_end + 1 :]), len(names)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--files", nargs="+", required=True)
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args(argv)

    known = fixture_names()
    total = 0
    for name in args.files:
        path = Path(name) if Path(name).is_absolute() else ROOT / name
        missing = [n for n in ruff_f821(path) if n in known]
        if not missing:
            continue
        result, changed = add_names(path.read_text(encoding="utf-8"), missing)
        if not args.dry_run:
            path.write_text(result, encoding="utf-8")
        print(f"{path.relative_to(ROOT)}: {', '.join(missing)}", file=sys.stderr)
        total += changed
    return 0 if total else 1


if __name__ == "__main__":
    sys.exit(main())
