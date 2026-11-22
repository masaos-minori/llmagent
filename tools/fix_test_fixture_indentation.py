"""tools/fix_test_fixture_indentation.py — Reindent the AgentConfig fixture blocks this batch inserted.

The bulk fixture rewrite matched the target text as a substring, so blocks inserted inside
indented method bodies kept the outer indentation and their surrounding statements did not.
This script sets every line of an inserted block to the indentation of the statement before it.

Usage:
    uv run python tools/fix_test_fixture_indentation.py <file>
"""

from __future__ import annotations

import sys
from pathlib import Path

MARKER = "# The Memory section owns the embedding endpoint"
BLOCK_FIRST = "ctx.cfg = AgentConfig("
BLOCK_FIELDS = (
    "llm=llm_cfg,",
    "memory=MemoryConfig(",
    "tool=tool_cfg,",
    "db=MIN_DB_CONFIG,",
    "maintenance=MIN_MAINTENANCE_CONFIG,",
)


def indent_of(line: str) -> int:
    return len(line) - len(line.lstrip())


def fix(path: Path) -> int:
    lines = path.read_text().split("\n")
    out: list[str] = []
    target = 0
    in_block = False
    just_after_block = False
    for line in lines:
        stripped = line.lstrip()
        if stripped.startswith(MARKER):
            target = indent_of(line)
            in_block = True
            out.append(" " * target + stripped)
            continue
        if in_block and (
            stripped.startswith(BLOCK_FIRST)
            or stripped in BLOCK_FIELDS
            or stripped == ")"
        ):
            width = target + 4 if stripped in BLOCK_FIELDS else target
            out.append(" " * width + stripped)
            if stripped == ")":
                in_block = False
                just_after_block = True
            continue
        if just_after_block and not in_block and indent_of(line) > target:
            out.append(" " * target + stripped)
            just_after_block = False
            continue
        out.append(line)
    path.write_text("\n".join(out))
    return sum(1 for a, b in zip(lines, out, strict=True) if a != b)


if __name__ == "__main__":
    for arg in sys.argv[1:]:
        print(f"{arg}: {fix(Path(arg))} line(s) reindented")
