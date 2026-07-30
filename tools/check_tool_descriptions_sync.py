#!/usr/bin/env python3
"""check_tool_descriptions_sync.py — Verify tools/TOOL_DESCRIPTIONS.md lists every tools/*.py file.

TOOL_DESCRIPTIONS.md is tools/'s own inventory doc. It is exactly as prone to
drift as any other documentation in this repo: a script can be added to
tools/ without updating it, or removed while a stale mention lingers. This
checker applies the same "compare the doc against the live directory" pattern
used by tools/gen_mcp_reference.py and tools/check_mcp_docs_consistency.py to
tools/ itself.

Usage:
    python tools/check_tool_descriptions_sync.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOOLS_DIR = REPO_ROOT / "tools"
DESCRIPTIONS_DOC = TOOLS_DIR / "TOOL_DESCRIPTIONS.md"

_BACKTICKED_PY_RE = re.compile(r"`([a-zA-Z0-9_]+\.py)`")

# Files intentionally excluded from the "must be documented" requirement.
_EXEMPT = frozenset({"__init__.py"})


def _live_tool_files() -> set[str]:
    return {p.name for p in TOOLS_DIR.glob("*.py") if p.name not in _EXEMPT}


def _documented_tool_files() -> set[str]:
    content = DESCRIPTIONS_DOC.read_text(encoding="utf-8")
    return set(_BACKTICKED_PY_RE.findall(content))


def main() -> int:
    if not DESCRIPTIONS_DOC.is_file():
        print(f"ERROR: {DESCRIPTIONS_DOC} not found.", file=sys.stderr)
        return 1

    live = _live_tool_files()
    documented = _documented_tool_files()

    undocumented = sorted(live - documented)
    stale = sorted(documented - live)

    for name in undocumented:
        print(
            f"[ERROR] {name}: exists in tools/ but is not mentioned in TOOL_DESCRIPTIONS.md"
        )
    for name in stale:
        print(
            f"[ERROR] {name}: mentioned in TOOL_DESCRIPTIONS.md but does not exist in tools/"
        )

    if undocumented or stale:
        print(
            f"\nFound {len(undocumented) + len(stale)} error(s).",
            file=sys.stderr,
        )
        return 1

    print("No issues found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
