#!/usr/bin/env python3
"""check_mcp_docs_consistency.py — Lightweight CI check for MCP documentation drift.

Runs consistency checks against .md files under docs/ and reports
errors with file:line references.  Exits non-zero if any errors found.

Checks:
    --all (default)       Run all checks
    --skip startup        Skip startup mode validation
    --skip failopen       Skip fail-open wording check for workflow_allowlist
    --skip routing        Skip routing authority language check
    --skip active         Skip active inconsistencies cross-reference check
    --skip toolcount      Skip tool count consistency check
    --skip discoveryrouting   Skip live-discovery-overrides-registry check
    --skip v1toolsrouting     Skip /v1/tools-as-routing-authority check
    --skip toolnamesrouting   Skip tool_names-as-routing-input check
    --skip auditformat        Skip audit log format check
    --skip transportiserror   Skip HttpTransport is_error=True check
    --skip stdiotransport     Skip stdio active transport reference check
    --skip watchdogrestart    Skip watchdog-restarts-on-dependency-failure check
    --skip strictskip         Skip strict-validation-skips-unreachable check

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

VALID_STARTUP_MODES: set[str] = {"none", "persistent", "subprocess"}

MCP_KNOWN_ISSUES_FILE = "04_mcp_90_inconsistencies_and_known_issues.md"

# Issue IDs intentionally not cross-referenced in other MCP docs.
# These are tracked in the known-issues file but not cited elsewhere because
# they are internal consistency notes, not operational guidance consumers need.
_ACTIVE_ISSUE_ALLOWLIST: frozenset[str] = frozenset(
    {
        "MCP-01",  # Startup mode terminology mismatch — internal note only
        "MCP-02",  # Routing authority mismatch — formatting inconsistency
        "MCP-04",  # Transport error / HealthRegistry mismatch — ambiguous parenthetical
        "MCP-06",  # Audit log format mismatch — two formats in same file
        "MCP-07",  # Health semantics ambiguity — diagram missing DEGRADED state
        "MCP-08",  # HTTP status code vs body fields mismatch
    },
)

HISTORICAL_MARKERS: frozenset[str] = frozenset(
    {"legacy", "historical", "archive only", "resolved", "was:", "removed"}
)

_STDIO_ALLOWLIST: frozenset[str] = frozenset(
    {
        "04_mcp_02_protocol_and_transport.md",
        "04_mcp_06_configuration_and_operations.md",
        "04_mcp_05_security_and_safety_model.md",
        "04_mcp_00_document-guide.md",
    }
)

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
    r"workflow_allowlist.*fail.open|fail.open.*workflow_allowlist",
    re.IGNORECASE,
)


def check_fail_open_workflow_allowlist(
    docs_dir: Path, files: list[DocFile]
) -> list[Issue]:
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
_SENTENCE_BOUNDARY = re.compile(r"[.!?:]")


def _check_routing_authority_in_sentence(sentence: str) -> bool:
    """Return True if *sentence* contains stale routing authority language."""
    # Check for "single source of truth" / "canonical authority" near ToolRegistry
    # within the same sentence, and require "routing" or "route" in that sentence.
    has_authority = bool(
        re.search(
            r"single\s+source\s+of\s+truth|canonical\s+(routing\s+)?authority",
            sentence,
            re.IGNORECASE,
        )
    )
    has_tool_registry = bool(re.search(r"ToolRegistry", sentence, re.IGNORECASE))
    has_routing = bool(re.search(r"routing|route", sentence, re.IGNORECASE))
    return has_authority and has_tool_registry and has_routing


def _find_sentences(line: str) -> list[str]:
    """Split a line into sentence-like chunks (by period/exclamation/question marks)."""
    parts = _SENTENCE_BOUNDARY.split(line)
    return [p.strip() for p in parts if p.strip()]


# Additional pattern: "primary routing layer" without the caveat about discovery map.
_PRIMARY_ROUTING_RE = re.compile(
    r"(primary\s+routing\s+l[a]?yer|main\s+routing\s+l[a]?yer)",
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
                context = doc.lines[i : i + 3] if i < len(doc.lines) else []
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
    r"^###\s+(MCP-\d+:\s+.+)$",
    re.MULTILINE,
)

_KNOWN_ISSUES_REFS_RE = re.compile(
    r"\[?(\d{2}_mcp_\d{2})\]?\s*:",
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

    # For each MCP doc file, check which active issues are referenced.
    # Match on the short ID prefix (e.g. "MCP-01"), not the full title.
    uncited: set[str] = set(active_issues.keys())
    for doc in files:
        if doc.rel_path == MCP_KNOWN_ISSUES_FILE:
            continue
        for line in doc.lines:
            for issue_full_title in list(uncited):
                short_id = issue_full_title.split(":")[0].strip()
                if short_id in line:
                    uncited.discard(issue_full_title)

    issues: list[Issue] = []
    for issue_id, line_no in sorted(active_issues.items()):
        short_id = issue_id.split(":")[0].strip()
        if issue_id in uncited and short_id not in _ACTIVE_ISSUE_ALLOWLIST:
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
# Check 5: Tool count consistency
# ---------------------------------------------------------------------------

_TOOL_COUNT_RE = re.compile(r"\bTools\((\d+)\)")

_SERVER_TOOLS_MAP: dict[str, frozenset[str]] = {
    "web-search-mcp": frozenset({"search_web"}),
    "file-read-mcp": frozenset(
        {
            "list_directory",
            "list_directory_with_sizes",
            "directory_tree",
            "read_text_file",
            "read_media_file",
            "read_multiple_files",
            "search_files",
            "grep_files",
            "get_file_info",
        }
    ),
    "file-write-mcp": frozenset(
        {"write_file", "edit_file", "create_directory", "move_file"}
    ),
    "file-delete-mcp": frozenset({"delete_file", "delete_directory"}),
    "github-mcp": frozenset(
        {
            "github_search_repositories",
            "github_get_file_contents",
            "github_create_branch",
            "github_create_issue",
            "github_add_issue_comment",
            "github_create_pull_request",
            "github_update_pull_request",
            "github_merge_pull_request",
            "github_create_or_update_file",
            "github_push_files",
            "github_delete_file",
        }
    ),
    "shell-mcp": frozenset({"shell_run"}),
    "mdq-mcp": frozenset(
        {
            "search_docs",
            "get_chunk",
            "outline",
            "index_paths",
            "refresh_index",
            "stats",
            "grep_docs",
            "fts_consistency_check",
            "fts_rebuild",
        }
    ),
    "rag-pipeline-mcp": frozenset(
        {
            "rag_run_pipeline",
            "rag_debug_pipeline",
            "rag_list_documents",
            "rag_delete_document",
        }
    ),
    "git-mcp": frozenset(
        {
            "git_status",
            "git_log",
            "git_diff",
            "git_branch",
            "git_show",
            "git_add",
            "git_commit",
            "git_checkout",
            "git_pull",
            "git_push",
        }
    ),
    "cicd-mcp": frozenset(
        {
            "trigger_workflow",
            "get_workflow_runs",
            "get_workflow_status",
            "get_workflow_logs",
        }
    ),
}


def check_tool_counts(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    """Check that documented tool counts in 04_mcp_04_server_catalog.md match
    the canonical frozenset definitions.

    Reports WARNING (not ERROR) to avoid brittleness when new tools are added.
    """
    catalog_file = None
    for doc in files:
        if doc.rel_path == "04_mcp_04_server_catalog.md":
            catalog_file = doc
            break

    if catalog_file is None:
        return [
            Issue(
                file="docs/",
                line_no=0,
                severity="WARNING",
                message="04_mcp_04_server_catalog.md not found — cannot verify tool counts.",
            )
        ]

    issues: list[Issue] = []
    for i, line in enumerate(catalog_file.lines, start=1):
        m = _TOOL_COUNT_RE.search(line)
        if m:
            server_section = _find_server_section_for_line(catalog_file, i)
            if server_section and server_section in _SERVER_TOOLS_MAP:
                expected_count = len(_SERVER_TOOLS_MAP[server_section])
                doc_count = int(m.group(1))
                if doc_count != expected_count:
                    issues.append(
                        Issue(
                            file=catalog_file.rel_path,
                            line_no=i,
                            severity="WARNING",
                            message=(
                                f"Tool count mismatch for {server_section}: "
                                f"documented {doc_count}, expected {expected_count}"
                            ),
                        )
                    )
    return issues


def _find_server_section_for_line(catalog: DocFile, line_no: int) -> str | None:
    """Find the server section name that contains the given line number."""
    for i, line in enumerate(catalog.lines, start=1):
        if i >= line_no:
            break
        m = re.match(r"^## (\S+)", line)
        if m:
            section_name = m.group(1).split("(")[0].strip()
            if section_name:
                current_section = section_name
    return locals().get("current_section")


# ---------------------------------------------------------------------------
# Shared helpers for new checks
# ---------------------------------------------------------------------------


def _is_historical_context(lines: list[str], line_idx: int) -> bool:
    """Return True if line_idx is within 10 lines of a historical section marker."""
    start = max(0, line_idx - 10)
    for i in range(start, line_idx):
        if any(marker in lines[i].lower() for marker in HISTORICAL_MARKERS):
            return True
    return False


# ---------------------------------------------------------------------------
# Check 6: Live discovery routing override
# ---------------------------------------------------------------------------

_DISCOVERY_OVERRIDES_RE = re.compile(
    r"discovery.*overrides.*registry|discovery\s+map.*wins",
    re.IGNORECASE,
)


def check_live_discovery_routing(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    """Detect stale language claiming live /v1/tools discovery overrides ToolRegistry."""
    issues: list[Issue] = []
    for doc in files:
        if doc.rel_path == MCP_KNOWN_ISSUES_FILE:
            continue
        for i, line in enumerate(doc.lines, start=1):
            if _DISCOVERY_OVERRIDES_RE.search(line):
                if _is_historical_context(doc.lines, i - 1):
                    continue
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="ERROR",
                        message=(
                            "Stale language: live discovery map no longer overrides ToolRegistry. "
                            "ToolRegistry is the sole routing authority."
                        ),
                    )
                )
    return issues


# ---------------------------------------------------------------------------
# Check 7: /v1/tools as routing authority
# ---------------------------------------------------------------------------

_V1TOOLS_AUTHORITY_RE = re.compile(
    r"/v1/tools.*routing\s+authority|/v1/tools.*single\s+source",
    re.IGNORECASE,
)


def check_routing_authority_v1tools(
    docs_dir: Path, files: list[DocFile]
) -> list[Issue]:
    """Detect stale language describing /v1/tools as the routing authority."""
    issues: list[Issue] = []
    for doc in files:
        for i, line in enumerate(doc.lines, start=1):
            if not _V1TOOLS_AUTHORITY_RE.search(line):
                continue
            if re.search(
                r"not.*routing\s+authority|not.*source\s+of\s+truth",
                line,
                re.IGNORECASE,
            ):
                continue
            issues.append(
                Issue(
                    file=doc.rel_path,
                    line_no=i,
                    severity="ERROR",
                    message=(
                        "Stale language: /v1/tools is not the routing authority. "
                        "ToolRegistry (tool_constants.py frozensets) is the sole routing source."
                    ),
                )
            )
    return issues


# ---------------------------------------------------------------------------
# Check 8: tool_names as routing input
# ---------------------------------------------------------------------------

_TOOL_NAMES_ROUTING_RE = re.compile(
    r"(?:tool_names.*(routing\s+input|routing\s+drives?|routing\s+determines?)"
    r"|(?:(?:routing\s+drives?|routing\s+determines?).*tool_names))"
)


def check_tool_names_routing_input(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    """Detect stale language describing tool_names as a routing input."""
    issues: list[Issue] = []
    for doc in files:
        if "04_mcp_90_" in doc.rel_path or "04_mcp_00_" in doc.rel_path:
            continue
        in_fenced_block = False
        for i, line in enumerate(doc.lines, start=1):
            if line.startswith("```"):
                in_fenced_block = not in_fenced_block
                continue
            if in_fenced_block:
                continue
            if not _TOOL_NAMES_ROUTING_RE.search(line):
                continue
            lower = line.lower()
            if "not a routing input" in lower or "not routing inputs" in lower:
                continue
            issues.append(
                Issue(
                    file=doc.rel_path,
                    line_no=i,
                    severity="ERROR",
                    message=(
                        "Stale language: tool_names is not a routing input. "
                        "It is drift validation metadata only."
                    ),
                )
            )
    return issues


# ---------------------------------------------------------------------------
# Check 9: Audit log single format
# ---------------------------------------------------------------------------

_AUDIT_KV_RE = re.compile(
    r"audit\.log.*key.value|AUDIT\s+session=.*format",
    re.IGNORECASE,
)
_AUDIT_SESSION_PROSE_RE = re.compile(r"AUDIT\s+session=")


def check_audit_log_single_format(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    """Detect stale audit log format language (key=value or plain AUDIT session= prose)."""
    issues: list[Issue] = []
    for doc in files:
        in_fenced_block = False
        for i, line in enumerate(doc.lines, start=1):
            if line.startswith("```"):
                in_fenced_block = not in_fenced_block
                continue
            if in_fenced_block:
                continue
            if _is_historical_context(doc.lines, i - 1):
                continue
            if _AUDIT_KV_RE.search(line):
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="ERROR",
                        message=(
                            "Stale audit log format: audit log uses JSON-lines, not key=value format."
                        ),
                    )
                )
            elif _AUDIT_SESSION_PROSE_RE.search(line):
                context = doc.lines[max(0, i - 4) : i + 3]
                has_json_caveat = any("json" in ctx.lower() for ctx in context)
                if not has_json_caveat:
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=i,
                            severity="ERROR",
                            message=(
                                "Stale audit log reference: AUDIT session= prose without "
                                "JSON/JSONL format caveat nearby."
                            ),
                        )
                    )
    return issues


# ---------------------------------------------------------------------------
# Check 10: HttpTransport is_error=True
# ---------------------------------------------------------------------------

_TRANSPORT_IS_ERROR_RE = re.compile(
    r"HttpTransport.*is_error\s*=\s*True|is_error=True.*transport",
    re.IGNORECASE,
)


def check_transport_error_is_error(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    """Detect docs claiming HttpTransport returns is_error=True for transport failures."""
    issues: list[Issue] = []
    for doc in files:
        if doc.rel_path == MCP_KNOWN_ISSUES_FILE:
            continue
        in_fenced_block = False
        for i, line in enumerate(doc.lines, start=1):
            if line.startswith("```"):
                in_fenced_block = not in_fenced_block
                continue
            if in_fenced_block:
                continue
            if not _TRANSPORT_IS_ERROR_RE.search(line):
                continue
            if "never" in line.lower() or "ToolCallResult" in line:
                continue
            issues.append(
                Issue(
                    file=doc.rel_path,
                    line_no=i,
                    severity="WARNING",
                    message=(
                        "Possible stale language: HttpTransport raises TransportError, "
                        "not is_error=True, for transport failures."
                    ),
                )
            )
    return issues


# ---------------------------------------------------------------------------
# Check 11: stdio active transport references
# ---------------------------------------------------------------------------

_STDIO_PATTERNS: list[tuple[re.Pattern[str], str]] = [
    (re.compile(r"(?:^|[^a-zA-Z])stdio(?:[^a-zA-Z]|$)"), "stdio"),
]


def check_stdio_active_transport(docs_dir: Path, files: list[DocFile]) -> list[Issue]:
    """Detect active stdio transport references in MCP docs outside the allowlist."""
    issues: list[Issue] = []
    for doc in files:
        if not doc.rel_path.startswith("04_mcp_"):
            continue
        if Path(doc.rel_path).name in _STDIO_ALLOWLIST:
            continue
        in_fenced_block = False
        for i, line in enumerate(doc.lines, start=1):
            if line.startswith("```"):
                in_fenced_block = not in_fenced_block
                continue
            if in_fenced_block:
                continue
            if _is_historical_context(doc.lines, i - 1):
                continue
            for pattern, label in _STDIO_PATTERNS:
                if pattern.search(line):
                    issues.append(
                        Issue(
                            file=doc.rel_path,
                            line_no=i,
                            severity="ERROR",
                            message=(
                                f"Active stdio transport reference ({label!r}) outside allowlist. "
                                "stdio is not an active transport in this project."
                            ),
                        )
                    )
                    break
    return issues


# ---------------------------------------------------------------------------
# Check 12: Watchdog restarts on dependency failure
# ---------------------------------------------------------------------------

_WATCHDOG_RESTART_RE = re.compile(
    r"watchdog.*restart.*dependency|dependency.*failure.*watchdog.*restart",
    re.IGNORECASE,
)


def check_watchdog_restarts_on_dependency_failure(
    docs_dir: Path, files: list[DocFile]
) -> list[Issue]:
    """Detect stale language claiming watchdog restarts on dependency failure."""
    issues: list[Issue] = []
    for doc in files:
        for i, line in enumerate(doc.lines, start=1):
            if _WATCHDOG_RESTART_RE.search(line):
                if _is_historical_context(doc.lines, i - 1):
                    continue
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="ERROR",
                        message=(
                            "Stale language: watchdog does not restart on dependency failure alone. "
                            "Restart is gated on restart_recommended=true in the /health body."
                        ),
                    )
                )
    return issues


# ---------------------------------------------------------------------------
# Check 13: strict validation skips unreachable
# ---------------------------------------------------------------------------

_STRICT_SKIP_RE = re.compile(
    r"strict.*skip.*unreachable|skip.*unreachable.*strict",
    re.IGNORECASE,
)


def check_strict_validation_skips_unreachable(
    docs_dir: Path, files: list[DocFile]
) -> list[Issue]:
    """Detect stale language claiming strict validation skips when all servers unreachable."""
    issues: list[Issue] = []
    for doc in files:
        for i, line in enumerate(doc.lines, start=1):
            if _STRICT_SKIP_RE.search(line):
                if _is_historical_context(doc.lines, i - 1):
                    continue
                if "RuntimeError" in line:
                    continue
                issues.append(
                    Issue(
                        file=doc.rel_path,
                        line_no=i,
                        severity="ERROR",
                        message=(
                            "Stale language: strict=True + all servers unreachable raises RuntimeError, "
                            "it does not skip validation."
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
    skip_choices = [
        "startup",
        "failopen",
        "routing",
        "active",
        "toolcount",
        "discoveryrouting",
        "v1toolsrouting",
        "toolnamesrouting",
        "auditformat",
        "transportiserror",
        "stdiotransport",
        "watchdogrestart",
        "strictskip",
    ]
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
    if "toolcount" not in skip:
        all_issues.extend(check_tool_counts(docs_dir, files))
    if "discoveryrouting" not in skip:
        all_issues.extend(check_live_discovery_routing(docs_dir, files))
    if "v1toolsrouting" not in skip:
        all_issues.extend(check_routing_authority_v1tools(docs_dir, files))
    if "toolnamesrouting" not in skip:
        all_issues.extend(check_tool_names_routing_input(docs_dir, files))
    if "auditformat" not in skip:
        all_issues.extend(check_audit_log_single_format(docs_dir, files))
    if "transportiserror" not in skip:
        all_issues.extend(check_transport_error_is_error(docs_dir, files))
    if "stdiotransport" not in skip:
        all_issues.extend(check_stdio_active_transport(docs_dir, files))
    if "watchdogrestart" not in skip:
        all_issues.extend(
            check_watchdog_restarts_on_dependency_failure(docs_dir, files)
        )
    if "strictskip" not in skip:
        all_issues.extend(check_strict_validation_skips_unreachable(docs_dir, files))

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
