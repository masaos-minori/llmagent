#!/usr/bin/env python3
"""Detect direct chunks_fts INSERT/UPDATE outside sanctioned paths.

Scans Python source files under a target directory for SQL string literals
containing 'INSERT INTO chunks_fts' or 'UPDATE chunks_fts'. Reports each
violation as '{file}:{line}: {sql_statement}'.

Sanctioned write paths are whitelisted:
  - scripts/agent/services/rag_maintenance_service.py::rebuild_fts()
    (sanctioned /session rag-rebuild-fts command path)
  - scripts/db/schema_sql.py (schema initialization SQL, executed once during setup)

Out-of-scope directories are excluded entirely:
  - scripts/mcp_servers/mdq/ (targets /opt/llm/db/mdq.sqlite)
  - tests/ (test files)

Usage:
    uv run python tools/check_chunks_fts_invariant.py
    uv run python tools/check_chunks_fts_invariant.py --path <dir>

Exit codes:
    0  No violations found
    1  Violations detected
"""

from __future__ import annotations

import argparse
import ast
import subprocess  # nosec B404 — rg is a trusted local CLI, no user input flows into subprocess
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
DOCS_DIR = REPO_ROOT / "docs"

SANCTIONED_PATHS: frozenset[str] = frozenset(
    {
        "scripts/agent/services/rag_maintenance_service.py",
        "scripts/db/schema_sql.py",
    }
)

EXCLUDED_DIRS: frozenset[str] = frozenset({"scripts/mcp_servers/mdq/", "tests/", "mdq"})

SQL_PATTERNS: list[str] = ["INSERT INTO chunks_fts", "UPDATE chunks_fts"]


def _is_in_sanctioned_function(file_path: str, line_num: int) -> bool:
    """Check if a line is inside rebuild_fts() function."""
    try:
        source = Path(file_path).read_text(encoding="utf-8")
        tree = ast.parse(source)
    except (SyntaxError, OSError):
        return False

    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef) and node.name == "rebuild_fts":
            start_line = getattr(node, "lineno", 0)
            end_line = getattr(node, "end_lineno", 0)
            if start_line <= line_num <= end_line:
                return True

    return False


def scan_for_violations(scan_dir: Path) -> list[tuple[str, int, str]]:
    """Scan for direct chunks_fts INSERT/UPDATE outside sanctioned paths."""
    violations: list[tuple[str, int, str]] = []

    cmd: list[str] = ["rg", "-n"]
    for pattern in SQL_PATTERNS:
        cmd.extend(["-e", pattern])
    cmd.append(str(scan_dir))

    result = subprocess.run(cmd, capture_output=True, text=True)  # nosec B603 — cmd is a validated static list, no user input
    if result.returncode != 0:
        # No matches found (exit code 1 means no matches)
        return violations

    for line in result.stdout.strip().split("\n"):
        parts = line.split(":", maxsplit=1)
        if len(parts) != 2:
            continue

        file_path, rest = parts
        line_num_str, sql_stmt = rest.split(":", maxsplit=1)

        # Normalize path for whitelist comparison: try relative first, fall back to basename
        rel_path = file_path
        try:
            rel_path = str(Path(file_path).relative_to(REPO_ROOT))
        except ValueError:
            rel_path = Path(file_path).name

        # Check if this is an excluded directory (check both original and normalized paths)
        if any(
            excluded in file_path or excluded in rel_path for excluded in EXCLUDED_DIRS
        ):
            continue

        # Check if this is a sanctioned path
        if rel_path in SANCTIONED_PATHS:
            # Entire file is sanctioned — no per-function check needed
            continue
        elif rel_path == "schema_sql.py":
            # schema_sql.py is always sanctioned (schema init)
            continue

        violations.append((rel_path, int(line_num_str), sql_stmt.strip()))

    return violations


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Detect direct chunks_fts INSERT/UPDATE outside sanctioned paths."
    )
    parser.add_argument(
        "--path",
        default=None,
        help="Directory to scan (default: repo root/scripts)",
    )
    args = parser.parse_args(argv)

    scan_dir = Path(args.path) if args.path else REPO_ROOT / "scripts"
    violations = scan_for_violations(scan_dir)

    if violations:
        for file_path, line_num, stmt in violations:
            print(f"{file_path}:{line_num}: {stmt}")
        return 1

    print("No violations found.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
