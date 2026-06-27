#!/usr/bin/env python3
"""check_mcp_docs_consistency.py — Lightweight CI check for MCP documentation drift.

Runs four consistency checks against .md files under docs/ and reports
errors with file:line references.  Exits non-zero if any errors found.

Checks:
    --all (default)  Run all checks
    --skip startup   Skip startup mode validation
    --skip failopen  Skip fail-open wording check for workflow_allowlist
    --skip routing   Skip routing authority language check
    --skip active    Skip active inconsistencies cross-reference check

Usage:
    python scripts/check_mcp_docs_consistency.py              # run all
    python scripts/check_mcp_docs_consistency.py --skip routing  # skip routing check
"""

from __future__ import annotations

import argparse
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

# ---------------------------------------------------------------------------
# Constants — mirror the canonical definitions in scripts/shared/mcp_config.py
# ---------------------------------------------------------------------------

VALID_STARTUP_MODES: set[str] = {"persistent", "ondemand", "subprocess"}

MCP_KNOWN_ISSUES_FILE = "04_mcp_90_inconsistencies_and_known_issues.md"

# ---------------------------------------------------------------------------
# Data helpers
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


def discover_md_files(docs_dir: Path) -> list[DocFile]:
    """Return all .md files under *docs_dir*, sorted for determinism."""
    result: list[DocFile] = []
    for p in sorted(docs_dir.rglob("*.md")):
        rel = str(p.relative_to(docs_dir))
        content = p.read_text(encoding="utf-8")
        lines = content.splitlines()
        result.append(DocFile(path=p, rel_path=rel, lines=lines))
    return result


# ---------------------------------------------------------------------------
# Check 1: Valid startup modes
# ---------------------------------------------------------------------------

_STARTUP_MODE_RE = re.compile(
    r'startup_mode\s*=\s*["\']([^"\']+)["\']',
)


def check_startup_modes(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    """Find startup_mode values that are not in VALID_STARTUP_MODES."""
    issues: list[Issue] = []
    for doc in files:
        for i, line in enumerate(doc.lines, start=1):
            m = _STARTUP_MODE_RE.search(line)
            if m is None:
                continue
            value = m.group(1).strip()
            if value not in VALID_STARTUP_MODES:
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="ERROR",
                        message=(
                            f"Unsupported startup_mode value: {value!r}. "
                            f"Valid values: {', '.join(sorted(VALID_STARTUP_MODES))}"
                        ),
                    )
                )
    return issues


# ---------------------------------------------------------------------------
# Check 2: Fail-open wording for workflow_allowlist
# ---------------------------------------------------------------------------

_FAIL_OPEN_ALLOWLIST_RE = re.compile(
    r'workflow_allowlist.*fail.open|fail.open.*workflow_allowlist',
    re.IGNORECASE,
)


def check_fail_open_workflow_allowlist(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    """Detect if workflow_allowlist is incorrectly described as fail-open.

    The cicd-mcp workflow_allowlist is fail-closed (empty = deny all).
    Any documentation that says it is fail-open is wrong.
    """
    issues: list[Issue] = []
    for doc in files:
        for i, line in enumerate(doc.lines, start=1):
            if _FAIL_OPEN_ALLOWLIST_RE.search(line):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="ERROR",
                        message=(
                            "workflow_allowlist is described as fail-open. "
                            "It should be fail-closed (empty = deny all)."
                        ),
                    )
                )
    return issues


# ---------------------------------------------------------------------------
# Check 3: Routing authority language
# ---------------------------------------------------------------------------

# Patterns that indicate stale routing authority language — ToolRegistry
# should NOT be described as the single source of truth or canonical authority
# for routing.  Only flag when ToolRegistry is mentioned in a routing context.
# Require "routing" to appear in the same sentence as the authority claim.
_SENTENCE_BOUNDARY = re.compile(r'[.!?:]')

def _check_routing_authority_in_sentence(sentence: str) -> bool:
    """Return True if *sentence* contains stale routing authority language."""
    # Check for "single source of truth" / "canonical authority" near ToolRegistry
    # within the same sentence, and require "routing" or "route" in that sentence.
    has_authority = bool(
        re.search(r'single\s+source\s+of\s+truth|canonical\s+(routing\s+)?authority',
                  sentence, re.IGNORECASE)
    )
    has_tool_registry = bool(re.search(r'ToolRegistry', sentence, re.IGNORECASE))
    has_routing = bool(re.search(r'routing|route', sentence, re.IGNORECASE))
    return has_authority and has_tool_registry and has_routing


def _find_sentences(line: str) -> list[str]:
    """Split a line into sentence-like chunks (by period/exclamation/question marks)."""
    parts = _SENTENCE_BOUNDARY.split(line)
    return [p.strip() for p in parts if p.strip()]

# Additional pattern: "primary routing layer" without the caveat about discovery map.
_PRIMARY_ROUTING_RE = re.compile(
    r'(primary\s+routing\s+l[a]?yer|main\s+routing\s+l[a]?yer)',
    re.IGNORECASE,
)

# Also flag if ToolRegistry is described as "primary routing layer" without the
# caveat about discovery map superseding it.  Check the next 3 lines for a
# mention of "discovery map" or "/v1/tools" to determine if the caveat exists.


def check_routing_authority(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    """Detect stale routing authority language referencing ToolRegistry.

    In the current architecture, ToolRegistry is Priority 2 (not Priority 1).
    The discovery map for live /v1/tools responses has superseded it as the
    primary routing source. Flag any text that calls ToolRegistry the
    'single source of truth' or 'canonical authority' in a routing context.
    """
    issues: list[Issue] = []
    for doc in files:
        for i, line in enumerate(doc.lines, start=1):
            sentences = _find_sentences(line)
            for sentence in sentences:
                if _check_routing_authority_in_sentence(sentence):
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=i,
                            severity="ERROR",
                            message=(
                                "Stale routing authority language: ToolRegistry is not "
                                "'single source of truth' or 'canonical authority'. "
                                "The discovery map for live /v1/tools responses has "
                                "superseded it as the primary routing source."
                            ),
                        )
                    )
            # Check for "primary routing layer" without caveat about discovery map
            if _PRIMARY_ROUTING_RE.search(line):
                # Look for caveat in next 3 lines
                has_caveat = False
                context = doc.lines[i:i+3] if i < len(doc.lines) else []
                for ctx_line in context:
                    if "discovery map" in ctx_line.lower() or "/v1/tools" in ctx_line:
                        has_caveat = True
                        break
                if not has_caveat:
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=i,
                            severity="WARNING",
                            message=(
                                "ToolRegistry described as 'primary routing layer' "
                                "without caveat about discovery map superseding it."
                            ),
                        )
                    )
    return issues


# ---------------------------------------------------------------------------
# Check 4: Active inconsistencies cross-reference
# ---------------------------------------------------------------------------

_ACTIVE_ISSUE_RE = re.compile(
    r'^###\s+(MCP-\d+:\s+.+)$',
    re.MULTILINE,
)

_KNOWN_ISSUES_REFS_RE = re.compile(
    r'\[?(\d{2}_mcp_\d{2})\]?\s*:',
)


def check_active_inconsistencies(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    """Check that active inconsistencies from the known-issues doc are
    referenced in other MCP docs.

    An inconsistency is 'active' if it appears under the '## Active Issues'
    header (not '## Resolved').  We verify each active issue is cited at
    least once across all MCP documentation files.
    """
    # Find the known-issues file
    issues_file = None
    for doc in files:
        if doc.rel_path == MCP_KNOWN_ISSUES_FILE:
            issues_file = doc
            break

    if issues_file is None:
        return [
            Issue(
                file="docs/",
                line_no=0,
                severity="WARNING",
                message=(
                    f"Known-issues file {MCP_KNOWN_ISSUES_FILE} not found in docs/ — "
                    "cannot verify cross-references."
                ),
            )
        ]

    # Parse active issue IDs from the known-issues file
    active_issues: dict[str, int] = {}  # id -> line_no in known-issues file
    in_active_section = False
    for i, line in enumerate(issues_file.lines, start=1):
        if line.strip() == "## Active Issues":
            in_active_section = True
            continue
        if line.strip().startswith("## ") and not line.strip().startswith("###"):
            in_active_section = False
            continue
        if in_active_section:
            m = _ACTIVE_ISSUE_RE.match(line)
            if m:
                issue_id = m.group(1).strip()
                active_issues[issue_id] = i

    # For each MCP doc file, check which active issues are referenced
    uncited: set[str] = set(active_issues.keys())
    for doc in files:
        if doc.rel_path == MCP_KNOWN_ISSUES_FILE:
            continue
        for line in doc.lines:
            for issue_id in list(uncited):
                if issue_id in line:
                    uncited.discard(issue_id)

    issues: list[Issue] = []
    for issue_id, line_no in sorted(active_issues.items()):
        if issue_id in uncited:
            issues.append(
                Issue(
                    file=issues_file.rel_path,
                    line_no=line_no,
                    severity="WARNING",
                    message=(
                        f"Active inconsistency {issue_id} is not referenced in any "
                        f"MCP documentation file."
                    ),
                )
            )
    return issues


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Check MCP documentation consistency.",
    )
    group = parser.add_mutually_exclusive_group()
    group.add_argument(
        "--docs-dir",
        default=None,
        help="Path to docs/ directory (default: <repo_root>/docs/)",
    )
    skip_choices = ["startup", "failopen", "routing", "active"]
    group.add_argument(
        "--skip",
        nargs="+",
        choices=skip_choices,
        help="Skip one or more checks",
    )
    args = parser.parse_args(argv)

    # Determine docs directory
    repo_root = Path(__file__).resolve().parent.parent
    docs_dir = Path(args.docs_dir) if args.docs_dir else repo_root / "docs"
    if not docs_dir.is_dir():
        print(f"ERROR: docs directory not found: {docs_dir}", file=sys.stderr)
        return 1

    files = discover_md_files(docs_dir)
    if not files:
        print("No .md files found in docs/.", file=sys.stderr)
        return 0

    skip = set(args.skip or [])
    all_issues: list[Issue] = []

    if "startup" not in skip:
        all_issues.extend(check_startup_modes(docs_dir, files))
    if "failopen" not in skip:
        all_issues.extend(check_fail_open_workflow_allowlist(docs_dir, files))
    if "routing" not in skip:
        all_issues.extend(check_routing_authority(docs_dir, files))
    if "active" not in skip:
        all_issues.extend(check_active_inconsistencies(docs_dir, files))

    # Report
    errors = [i for i in all_issues if i.severity == "ERROR"]
    warnings = [i for i in all_issues if i.severity == "WARNING"]
    if all_issues:
        for issue in all_issues:
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
