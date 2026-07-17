#!/usr/bin/env python3
"""check_agent_docs_consistency.py — Lightweight CI check for Agent documentation drift.

Mirrors tools/check_mcp_docs_consistency.py's architecture (typed DocFile/Issue
dataclasses, one function per check, --skip flag registry, ERROR/WARNING
severity). Runs consistency checks against docs/05_agent_*.md (and, for the
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
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Data helpers — mirror tools/check_mcp_docs_consistency.py's shapes
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DocFile:
    """A single documentation file with its contents."""

    path: Path
    rel_path: str  # relative to docs/
    lines: list[str] = field(default_factory=list)

    @property
    def line_count(self) -> int:
        return len(self.lines)


@dataclass(frozen=True)
class Issue:
    """A single consistency issue found."""

    file: str  # relative path within docs/
    line_no: int
    severity: str  # "ERROR" or "WARNING"
    message: str


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------


def discover_md_files(docs_dir: Path, *, prefix: str) -> list[DocFile]:
    """Return all *prefix*-matching .md files under *docs_dir*, sorted for determinism."""
    result: list[DocFile] = []
    for p in sorted(docs_dir.glob(f"{prefix}*.md")):
        rel = str(p.relative_to(docs_dir))
        content = p.read_text(encoding="utf-8")
        lines = content.splitlines()
        result.append(DocFile(path=p, rel_path=rel, lines=lines))
    return result


# ---------------------------------------------------------------------------
# Check 1: Broken internal Markdown links (also covers removed-file refs
# expressed as [text](path.md) links, since a removed file simply fails to
# resolve here)
# ---------------------------------------------------------------------------

_MD_LINK_RE = re.compile(r"\[[^\]]*\]\(([^)]+)\)")


def _split_link_target(target: str) -> tuple[str, str | None]:
    """Split a link target into (file_part, anchor_part_or_None)."""
    if "#" in target:
        file_part, _, anchor = target.partition("#")
        return file_part, anchor
    return target, None


def check_broken_internal_links(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    """Flag [text](path.md) / [text](path.md#anchor) links that don't resolve."""
    issues: list[Issue] = []
    existing_files = {f.name for f in docs_dir.glob("*.md")}

    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            for match in _MD_LINK_RE.finditer(line):
                target = match.group(1).strip()
                # Skip external links and mailto/anchors-only-on-current-page checks
                # that don't reference another doc file.
                if target.startswith(("http://", "https://", "mailto:")):
                    continue
                file_part, _anchor = _split_link_target(target)
                if not file_part:
                    continue  # pure "#anchor" link within the same page
                if "/" in file_part:
                    continue  # relative paths outside docs/ are out of scope
                if file_part not in existing_files:
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=line_no,
                            severity="ERROR",
                            message=(
                                f"broken internal link target {file_part!r} "
                                f"(referenced doc file does not exist under docs/)"
                            ),
                        )
                    )
    return issues


# ---------------------------------------------------------------------------
# Check 2: Removed-legacy-doc-file reference prohibition (bare filename
# mentions, not wrapped in a Markdown link — e.g. inline-code `old_file.md`)
# ---------------------------------------------------------------------------

_BARE_MD_FILENAME_RE = re.compile(r"`(0[0-9]_[a-z0-9_-]+\.md)`")


def check_removed_file_references(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    """Flag inline-code-quoted `NN_doc_name.md` mentions of files that don't exist.

    Skips lines explicitly marked as historical ("削除済み" = "already
    removed") -- this doc set's established convention for intentionally
    naming a removed file as migration context (see e.g.
    05_agent_00_document-guide.md's "Canonical Source Rules" section).
    """
    issues: list[Issue] = []
    existing_files = {f.name for f in docs_dir.glob("*.md")}

    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            if "削除済み" in line:
                continue
            for match in _BARE_MD_FILENAME_RE.finditer(line):
                filename = match.group(1)
                if filename not in existing_files:
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=line_no,
                            severity="ERROR",
                            message=(
                                f"reference to removed/nonexistent doc file `{filename}`"
                            ),
                        )
                    )
    return issues


# ---------------------------------------------------------------------------
# Check 3: Slash-command drift vs command_defs_list.py's _COMMANDS
# ---------------------------------------------------------------------------

_COMMAND_DEF_RE = re.compile(r'CommandDef\(\s*"(/[a-z][a-z0-9_]*)"')
_DOC_SLASH_COMMAND_RE = re.compile(
    r"(?<![`/a-zA-Z0-9])/(mcp|db|debug|audit|memory|mdq|rag|plugin|help|config|"
    r"stats|set|reload|context|compact|system|session|clear|undo|history|"
    r"export|plan|approve|reject|skill)\b"
)


def _extract_registered_command_names(repo_root: Path) -> frozenset[str] | None:
    """Regex-extract slash command names from command_defs_list.py's CommandDef(...) calls.

    Returns None if the source file cannot be found (best-effort; the caller
    should skip the check rather than fail noisily).
    """
    src = repo_root / "scripts" / "agent" / "commands" / "command_defs_list.py"
    if not src.is_file():
        return None
    content = src.read_text(encoding="utf-8")
    return frozenset(_COMMAND_DEF_RE.findall(content))


def check_command_drift(
    docs_dir: Path, files: list[DocFile], repo_root: Path
) -> list[Issue]:
    """Flag doc-referenced /command names not present in _COMMANDS (WARNING).

    Best-effort: only checks a fixed set of command-name keywords (see
    _DOC_SLASH_COMMAND_RE) to avoid false positives on generic paths like
    "/opt/llm" or URL paths that happen to start with a slash. Skips lines
    marked historical ("removed", "旧" = "former", "削除済み" = "already
    removed") -- this doc set's established convention for citing a removed
    command as migration context (see e.g. 05_agent_07_07's migration notes).
    """
    registered = _extract_registered_command_names(repo_root)
    if registered is None:
        return []

    issues: list[Issue] = []
    for doc in files:
        for line_no, line in enumerate(doc.lines, start=1):
            if "旧" in line or "削除済み" in line or "removed" in line.lower():
                continue
            for match in _DOC_SLASH_COMMAND_RE.finditer(line):
                cmd = f"/{match.group(1)}"
                if cmd == "/exit":
                    continue  # REPL-reserved, not in _COMMANDS by design
                if cmd not in registered:
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=line_no,
                            severity="WARNING",
                            message=(
                                f"doc references {cmd!r} which is not a "
                                f"registered command in _COMMANDS "
                                f"(command_defs_list.py)"
                            ),
                        )
                    )
    return issues


# ---------------------------------------------------------------------------
# Check 4: DB-schema drift vs schema_sql.py (best-effort)
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
# Check 5: Obsolete diagnostics / audit-event references (best-effort)
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

    errors = [i for i in all_issues if i.severity == "ERROR"]
    warnings = [i for i in all_issues if i.severity == "WARNING"]
    if all_issues:
        for issue in sorted(all_issues, key=lambda i: (i.file, i.line_no)):
            print(f"[{issue.severity}] {issue.file}:{issue.line_no}: {issue.message}")
        parts = []
        if errors:
            parts.append(f"{len(errors)} error(s)")
        if warnings:
            parts.append(f"{len(warnings)} warning(s)")
        print(f"\nFound {', '.join(parts)}.", file=sys.stderr)
    else:
        print("No issues found.")

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
