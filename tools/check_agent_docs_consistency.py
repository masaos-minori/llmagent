#!/usr/bin/env python3
"""check_agent_docs_consistency.py — Lightweight CI check for Agent documentation drift.

Shares its DocFile/Issue dataclasses, file discovery, and generic checks
(broken links, removed-file references, slash-command drift) with
tools/check_mcp_docs_consistency.py via tools/_docs_consistency_lib.py.
Runs consistency checks against docs/05_agent_*.md (and, for the
DB-schema-drift check, docs/90_shared_04_*.md) and reports errors with
file:line references. Exits non-zero if any ERROR-severity issues are found.

Checks:
    --all (default)          Run all checks
    --skip links              Skip broken internal Markdown link detection
    --skip removedfiles       Skip removed-legacy-doc-file reference check
    --skip commanddrift       Skip slash-command drift vs command_defs_list.py (WARNING)
    --skip schemadrift        Skip DB-schema drift vs schema_sql.py (best-effort, WARNING)
    --skip diagnostics        Skip obsolete diagnostics/event-name reference check (WARNING)

Usage:
    python tools/check_agent_docs_consistency.py                 # run all
    python tools/check_agent_docs_consistency.py --skip schemadrift
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

if __package__ in (None, ""):
    # Allow `python tools/check_agent_docs_consistency.py` (script form, as
    # used by .github/workflows/agent-docs-consistency.yml) in addition to
    # `python -m tools.check_agent_docs_consistency` / the pyproject.toml
    # console-script entry point, both of which set up the package import
    # path automatically.
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from tools._docs_consistency_lib import (
    DocFile,
    Issue,
    check_broken_internal_links,
    check_command_drift,
    check_removed_file_references,
    discover_md_files,
    report_and_exit,
)

# ---------------------------------------------------------------------------
# Check: DB-schema drift vs schema_sql.py (best-effort)
# ---------------------------------------------------------------------------

_CREATE_TABLE_RE = re.compile(
    r"CREATE (?:VIRTUAL )?TABLE(?: IF NOT EXISTS)? ([a-z_][a-z0-9_]*)",
    re.IGNORECASE,
)
_DOC_TABLE_MENTION_RE = re.compile(r"`([a-z_][a-z0-9_]*)`\s*テーブル")


def _extract_schema_table_names(repo_root: Path) -> frozenset[str] | None:
    """Regex-extract CREATE TABLE / CREATE VIRTUAL TABLE names from schema_sql.py."""
    src = repo_root / "scripts" / "db" / "schema_sql.py"
    if not src.is_file():
        return None
    content = src.read_text(encoding="utf-8")
    return frozenset(_CREATE_TABLE_RE.findall(content))


def check_schema_drift(docs_dir: Path, repo_root: Path) -> list[Issue]:
    """Flag doc-mentioned `table_name`テーブル references not in schema_sql.py (WARNING).

    Best-effort: relies on the "`table_name`テーブル" phrasing convention used
    in docs/90_shared_04_*.md and docs/05_agent_09_*.md; does not attempt a
    full column-level diff.
    """
    table_names = _extract_schema_table_names(repo_root)
    if table_names is None:
        return []

    issues: list[Issue] = []
    target_files = discover_md_files(
        docs_dir, prefix="90_shared_04_"
    ) + discover_md_files(docs_dir, prefix="05_agent_09_")
    for doc in target_files:
        for line_no, line in enumerate(doc.lines, start=1):
            for match in _DOC_TABLE_MENTION_RE.finditer(line):
                name = match.group(1)
                if name not in table_names:
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=line_no,
                            severity="WARNING",
                            message=(
                                f"doc mentions table `{name}` which does not "
                                f"appear in schema_sql.py's CREATE TABLE "
                                f"statements (best-effort check; verify manually)"
                            ),
                        )
                    )
    return issues


# ---------------------------------------------------------------------------
# Check: Obsolete diagnostics / audit-event references (best-effort)
# ---------------------------------------------------------------------------

_EVENT_KIND_DEF_RE = re.compile(
    r'(?:"event":\s*"([a-z_]+)"|event\s*=\s*"([a-z_]+)"|kind\s*=\s*"([a-z_]+)"'
    r'|\.save\(\s*[^,]+,\s*"([a-z_]+)"\s*,)'
)
_DOC_EVENT_MENTION_RE = re.compile(r'"event":\s*"([a-z_]+)"|kind="([a-z_]+)"')


def _extract_known_event_kinds(repo_root: Path) -> frozenset[str]:
    """Regex-extract audit "event" / diagnostic "kind" string literals from agent/*.py."""
    found: set[str] = set()
    agent_dir = repo_root / "scripts" / "agent"
    if not agent_dir.is_dir():
        return frozenset()
    for py_file in agent_dir.rglob("*.py"):
        content = py_file.read_text(encoding="utf-8")
        for match in _EVENT_KIND_DEF_RE.finditer(content):
            for group in match.groups():
                if group:
                    found.add(group)
    return frozenset(found)


def check_obsolete_diagnostics_references(
    docs_dir: Path, files: list[DocFile], repo_root: Path
) -> list[Issue]:
    """Flag doc-mentioned event/diagnostic kind names not found in agent/*.py (WARNING).

    Best-effort, seeded from docs/05_agent_90_inconsistencies_and_known_issues.md's
    format description rather than a maintained issue-ID allowlist (that file
    currently has no numbered entries to seed from).
    """
    known = _extract_known_event_kinds(repo_root)
    if not known:
        return []

    issues: list[Issue] = []
    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            for match in _DOC_EVENT_MENTION_RE.finditer(line):
                name = match.group(1) or match.group(2)
                if name and name not in known:
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=line_no,
                            severity="WARNING",
                            message=(
                                f"doc references event/diagnostic kind "
                                f"{name!r} not found as a string literal "
                                f"under scripts/agent/ (best-effort check; "
                                f"verify manually)"
                            ),
                        )
                    )
    return issues


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check Agent documentation consistency.",
    )
    parser.add_argument(
        "--docs-dir",
        default=None,
        help="Path to docs/ directory (default: <repo_root>/docs/)",
    )
    skip_choices = [
        "links",
        "removedfiles",
        "commanddrift",
        "schemadrift",
        "diagnostics",
    ]
    parser.add_argument(
        "--skip",
        nargs="+",
        choices=skip_choices,
        help="Skip one or more checks",
    )
    args = parser.parse_args(argv)

    repo_root = Path(__file__).resolve().parent.parent
    docs_dir = Path(args.docs_dir) if args.docs_dir else repo_root / "docs"
    if not docs_dir.is_dir():
        print(f"ERROR: docs directory not found: {docs_dir}", file=sys.stderr)
        return 1

    files = discover_md_files(docs_dir, prefix="05_agent_")
    if not files:
        print("No 05_agent_*.md files found in docs/.", file=sys.stderr)
        return 0

    skip = set(args.skip or [])
    all_issues: list[Issue] = []

    if "links" not in skip:
        all_issues.extend(check_broken_internal_links(docs_dir, files))
    if "removedfiles" not in skip:
        all_issues.extend(check_removed_file_references(docs_dir, files))
    if "commanddrift" not in skip:
        all_issues.extend(check_command_drift(docs_dir, files, repo_root))
    if "schemadrift" not in skip:
        all_issues.extend(check_schema_drift(docs_dir, repo_root))
    if "diagnostics" not in skip:
        all_issues.extend(
            check_obsolete_diagnostics_references(docs_dir, files, repo_root)
        )

    return report_and_exit(all_issues)


if __name__ == "__main__":
    sys.exit(main())
