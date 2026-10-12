#!/usr/bin/env python3
"""check_tool_descriptions_sync.py — Verify tools/TOOL_DESCRIPTIONS.md lists every tools/*.py file.

TOOL_DESCRIPTIONS.md is tools/'s own inventory doc. It is exactly as prone to
drift as any other documentation in this repo: a script can be added to
tools/ without updating it, or removed while a stale mention lingers. This
checker applies the same "compare the doc against the live directory" pattern
used by tools/generate_reference_table.py and tools/check_mcp_docs_consistency.py to
tools/ itself.

It also verifies that every `tools/<name>.py` path or `python -m tools.<name>`
module referenced from CI/hook configuration (`.github/workflows/*.yml`,
`.pre-commit-config.yaml`, `tox.ini`) still exists, so a tool rename cannot leave
a workflow command or `paths:` trigger pointing at a file that is gone.

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

# `tools/<name>.py` paths and `-m tools.<name>` modules in CI/hook configuration.
_CONFIG_TOOL_REF_RE = re.compile(r"tools/([A-Za-z0-9_]+)\.py|-m tools\.([A-Za-z0-9_]+)")
_CONFIG_GLOBS = (".github/workflows/*.yml", ".pre-commit-config.yaml", "tox.ini")

# Files intentionally excluded from the "must be documented" requirement.
_EXEMPT = frozenset({"__init__.py"})


def _live_tool_files() -> set[str]:
    return {p.name for p in TOOLS_DIR.glob("*.py") if p.name not in _EXEMPT}


def _documented_tool_files() -> set[str]:
    content = DESCRIPTIONS_DOC.read_text(encoding="utf-8")
    return set(_BACKTICKED_PY_RE.findall(content))


def find_dangling_config_references(
    repo_root: Path = REPO_ROOT,
) -> list[tuple[str, int, str]]:
    """Return `(config_file, line_no, tool_file)` for each reference to a missing tool."""
    live = {p.name for p in (repo_root / "tools").glob("*.py")}
    dangling: list[tuple[str, int, str]] = []
    for pattern in _CONFIG_GLOBS:
        for config in sorted(repo_root.glob(pattern)):
            lines = config.read_text(encoding="utf-8").splitlines()
            for line_no, line in enumerate(lines, start=1):
                for match in _CONFIG_TOOL_REF_RE.finditer(line):
                    name = f"{match.group(1) or match.group(2)}.py"
                    if name not in live:
                        rel = config.relative_to(repo_root).as_posix()
                        dangling.append((rel, line_no, name))
    return dangling


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

    dangling = find_dangling_config_references()
    for config, line_no, name in dangling:
        print(
            f"[ERROR] {config}:{line_no}: references tools/{name}, which does not exist"
        )

    total = len(undocumented) + len(stale) + len(dangling)
    if total:
        print(
            f"\nFound {total} error(s).",
            file=sys.stderr,
        )
        return 1

    print("No issues found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
