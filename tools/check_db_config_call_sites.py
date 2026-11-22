#!/usr/bin/env python3
"""check_db_config_call_sites.py — Verify SQLiteHelper call sites supply typed configuration.

Contract (Plan agentcfg004, REQ-003 / AC-004, ADR-008 configuration ownership):
`scripts/db/` resolves no configuration file. Every `SQLiteHelper(...)` call site in
`scripts/` must receive the typed configuration from the process that owns the
configuration file, so each call supplies either:

  * `db_config=`  — the typed `DbConfig` built from the caller's mapping, or
  * `db_path=`    — the self-contained path exception (a caller that holds its own
                    configuration file, e.g. an MCP server).

A call site with neither is a violation: `db.helper.SQLiteHelper` raises at runtime
when no path can be resolved, and the implicit `agent.toml` load that used to supply
it is gone.

Scope: `scripts/` only. `tests/` constructs typed configurations directly, which this
checker does not inspect. Call sites inside `scripts/db/helper.py` itself are excluded
(the class definition is the contract).

Rule: plans/done/20261121-140444_agentcfg004_config-ownership-split.md REQ-003, AC-004.

Usage:
    uv run python tools/check_db_config_call_sites.py
    uv run python tools/check_db_config_call_sites.py --format json

Exit codes:
    0  No violations found
    1  Violations detected
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = ROOT / "scripts"
HELPER_FILE = "db/helper.py"

#: Names whose call sites may construct a helper without a supplied configuration.
_TARGET_NAMES = {"SQLiteHelper", "_FakeSQLiteHelper"}


def _scan_file(path: Path) -> list[dict[str, object]]:
    """Return one violation record per SQLiteHelper call that supplies neither
    db_config= nor db_path=; a call inside the helper module itself is not reported."""
    rel = path.relative_to(SCRIPTS_DIR).as_posix()
    if rel == HELPER_FILE:
        return []
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        return [{"file": rel, "line": 0, "detail": f"could not parse: {exc}"}]

    violations: list[dict[str, object]] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = (
            func.id
            if isinstance(func, ast.Name)
            else (func.attr if isinstance(func, ast.Attribute) else None)
        )
        if name not in _TARGET_NAMES:
            continue
        keywords = {kw.arg for kw in node.keywords if kw.arg}
        if "db_config" in keywords or "db_path" in keywords:
            continue
        violations.append(
            {
                "file": rel,
                "line": node.lineno,
                "detail": f"{name}(...) called without db_config= or db_path=",
            }
        )
    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    parser.add_argument("--format", choices=["text", "json"], default="text")
    args = parser.parse_args(argv)

    violations: list[dict[str, object]] = []
    for path in sorted(SCRIPTS_DIR.rglob("*.py")):
        violations.extend(_scan_file(path))

    if args.format == "json":
        print(json.dumps({"violations": violations}, indent=2))
    else:
        if violations:
            print(f"SQLiteHelper call-site contract violations ({len(violations)}):")
            for v in violations:
                print(f"  scripts/{v['file']}:{v['line']}: {v['detail']}")
        else:
            print("No SQLiteHelper call-site violations.")

    return 1 if violations else 0


if __name__ == "__main__":
    sys.exit(main())
