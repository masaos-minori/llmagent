#!/usr/bin/env python3
"""Audit Implementation Target Files paths in plans/*.md against the working tree.

Flags target paths that do not exist unless the row's change type is a creation
(create / new). Read-only diagnostic; run with: uv run python3 tools/audit_plan_target_paths.py [plans/*.md ...]
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

ROW_RE = re.compile(r"^\|\s*(`?)([^|`]+?)\1\s*\|([^|]*)\|")
CREATE_HINTS = ("create", "new", "generated", "manifest;", "registry;")


def audit(path: Path) -> list[str]:
    findings: list[str] = []
    in_table = False
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if line.startswith("## Implementation Target Files"):
            in_table = True
            continue
        if (
            in_table
            and line.startswith("## ")
            and "Implementation Target Files" not in line
        ):
            in_table = False
        if not in_table:
            continue
        m = ROW_RE.match(line)
        if not m:
            continue
        target = m.group(2).strip()
        rest = m.group(3).lower()
        if not target or target.startswith(("File Path", "---", "Change Type")):
            continue
        if target.startswith("registry/") and not Path(target).exists():
            # registry/ is a planned new directory; still report as create-only
            if not any(h in rest for h in CREATE_HINTS):
                findings.append(f"{path.name}:{i}: missing (no create hint): {target}")
            continue
        if "/" not in target and "." not in target:
            continue
        if Path(target).exists():
            continue
        if any(h in rest for h in CREATE_HINTS):
            continue
        findings.append(f"{path.name}:{i}: missing target path: {target}")
    return findings


def main() -> int:
    args = sys.argv[1:]
    plans = [Path(a) for a in args] if args else sorted(Path("plans").glob("*.md"))
    total = 0
    for p in plans:
        for f in audit(p):
            print(f)
            total += 1
    print(f"{total} finding(s) across {len(plans)} plan(s).")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main())
