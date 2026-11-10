#!/usr/bin/env python3
"""One-shot fixture migration for the adrrev004 batch (rows 80/81/92/93 pattern).

For each target test file:
  1. Replace `STRICT_PRODUCTION_OVERRIDES,` with `PERMISSIVE_ALLOWED_ROOT,` in
     the `from tests.agent._config_test_defaults import (...)` block.
  2. Remove the `**STRICT_PRODUCTION_OVERRIDES,` spread line in the
     `build_agent_config({...})` dict.
  3. Insert `"allowed_root": PERMISSIVE_ALLOWED_ROOT,` just before `**overrides,`
     (only if the dict has no `allowed_root` entry already).

Aborts with a nonzero exit if any expected anchor is missing or ambiguous, so
the change is never applied "papered over".
"""

from __future__ import annotations

import sys
from pathlib import Path

IMPORT_OLD = "    STRICT_PRODUCTION_OVERRIDES,\n"
IMPORT_NEW = "    PERMISSIVE_ALLOWED_ROOT,\n"
SPREAD_OLD = "            **STRICT_PRODUCTION_OVERRIDES,\n"
OVERRIDES_ANCHOR = "            **overrides,\n"
ALLOWED_ROOT_NEW = '            "allowed_root": PERMISSIVE_ALLOWED_ROOT,\n'


def migrate(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    notes: list[str] = []

    def once(old: str, new: str, what: str) -> str:
        count = text.count(old)
        if count != 1:
            raise SystemExit(f"{path}: {what} anchor found {count} times, expected 1")
        return text.replace(old, new, 1)

    if "from tests.agent._config_test_defaults import (" not in text:
        raise SystemExit(f"{path}: _config_test_defaults import block missing")
    text = once(IMPORT_OLD, IMPORT_NEW, "import name")
    notes.append("import name swapped")

    if SPREAD_OLD in text:
        text = text.replace(SPREAD_OLD, "", 1)
        notes.append("strict spread removed")
    else:
        raise SystemExit(f"{path}: strict spread anchor missing")

    if '"allowed_root"' in text.split("**overrides")[0]:
        notes.append("allowed_root already present in base dict: not inserted")
    else:
        text = once(OVERRIDES_ANCHOR, ALLOWED_ROOT_NEW + OVERRIDES_ANCHOR, "overrides")
        notes.append("PERMISSIVE_ALLOWED_ROOT added")

    path.write_text(text, encoding="utf-8")
    return notes


def main(argv: list[str]) -> int:
    for arg in argv:
        path = Path(arg)
        notes = migrate(path)
        print(f"{path}: {'; '.join(notes)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
