#!/usr/bin/env python3
"""tools/check_compat_shims.py

CI check for backward compatibility leftovers in active source code and docs:
- Backward compatibility references
- Re-export stubs
- Stale import paths (rag.models, rag.llm)
- Module-level _cfg cache references

Usage:
    python -m tools.check_compat_shims [--allowlist <path>]
"""

from __future__ import annotations

import argparse
import ast
import re
import sys
import tomllib
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tools._docs_consistency_lib import Issue

ROOT_DIR = Path(__file__).resolve().parent.parent

# Allow running as a bare script (`python tools/check_compat_shims.py`) in
# addition to `python -m tools.check_compat_shims`: make the repo root
# importable so the `from tools._docs_consistency_lib import ...` in
# check_doc_symbols() resolves when the script's own directory (not the repo
# root) is sys.path[0].
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

# Patterns that should not appear in active source code or docs
COMPAT_PATTERNS = {
    "backward compatibility layer": r"backward[ _]compatibility\s+(?:layer|stub|re-export)",
    "from rag.models import": r"from\s+rag\.models\s+import",
    "import rag.models": r"import\s+rag\.models\b",
    "rag.llm import": r"from\s+rag\.llm\s+import",
    "rag.llm module": r"import\s+rag\.llm\b",
    "module-level _cfg": r"module[ _]level[ _]_cfg",
    "_cfg cache": r"_cfg[ _]cache",
    "compatibility/emergency": r"compatibility/emergency",
    "Static fallback": r"[Ss]tatic\s+fallback",
    "_SET_ROUTES": r"_SET_ROUTES",
    "_fallback_route": r"_fallback_route",
    "_GITHUB_PREFIX": r"_GITHUB_PREFIX",
    "github_ prefix exception": r"github_[ _]prefix\s+exception",
    "rag.pipeline._cfg": r"rag\.pipeline\._cfg",
    "/mcp install": r"/mcp[ _]install",
    "POST /v1/search": r"POST\s+/v1/search",
    "/note command": r"/note\s+(add|list|delete|pin|unpin|search)",
    "/db urls alias": r"/db\s+urls\b(?!.*rag|session)",
    "/db clean alias": r"/db\s+clean\b(?!.*rag|session)",
    "/db rebuild-fts alias": r"/db\s+rebuild-fts\b(?!.*rag|session)",
    "/db recover alias": r"/db\s+recover\b(?!.*rag|session)",
    "/mdq command": r"(?<![\w/.-])/mdq(?![\w./-])",
    "approval_ops (post-execution approval stage removed)": r"\bapproval_ops\b",
    "request_approval (post-execution approval stage removed)": r"\brequest_approval\b",
    "_gate_approval (post-execution approval stage removed)": r"\b_gate_approval\b",
    "find_latest_pending_approval (post-execution approval stage removed)": r"\bfind_latest_pending_approval\b",
    "_recover_pending_approvals (post-execution approval stage removed)": r"\b_recover_pending_approvals\b",
    "WorkflowPendingApprovalError (post-execution approval stage removed)": r"\bWorkflowPendingApprovalError\b",
    "ApprovalRecord (post-execution approval stage removed)": r"\bApprovalRecord\b",
    "pending_approval_id (post-execution approval stage removed)": r"\bpending_approval_id\b",
    "pending_approval_task_id (post-execution approval stage removed)": r"\bpending_approval_task_id\b",
    "ApprovalRecovery (post-execution approval stage removed)": r"\bApprovalRecovery\b",
    "startup_approval_recovery (post-execution approval stage removed)": r"\bstartup_approval_recovery\b",
    "approval_requested (post-execution approval stage removed)": r"\bapproval_requested\b",
    "approval_pending (post-execution approval stage removed)": r"\bapproval_pending\b",
    "/approve command": r"(?<![\w/.-])/approve(?![\w./-])",
    "/reject command": r"(?<![\w/.-])/reject(?![\w./-])",
    "auto_inject_notes": r"auto_inject_notes",
    "notes table": r"notes[ _]table",
    "_MCP_TOOLS": r"_MCP_TOOLS",
    # Shared/DB schema cleanup — stale references after plan 54 (workflow_schema.py removal)
    "db.workflow_schema import": r"from\s+db\.workflow_schema\s+import",
    "import db.workflow_schema": r"import\s+db\.workflow_schema\b",
    "python -m db.workflow_schema": r"python\s+-m\s+db\.workflow_schema",
    "workflow_schema.py reference": r"db/workflow_schema\.py",
    "07_ref-sqlite.md reference": r"07_ref-sqlite\.md",
    "07_spec_db.md reference": r"07_spec_db\.md",
    # Shared/DB schema cleanup — stale issue IDs after plan 58 (DOCMISS-01, UNDOC-03, TYPE-01 removed)
    "stale issue ID": r"(?:DOCMISS-01|UNDOC-03|TYPE-01|UNIMPL-01)",
    # Shared/DB schema cleanup — stale eventbus direct SQL load after plan 55 (init_db unified)
    "eventbus schema.sql direct load": r"\.read\s+eventbus/schema\.sql",
    # plan 56 patterns — backward-compat stub phrases
    "re-export stub phrase": r"re-export\s+stub",
    "compatibility shim phrase": r"compatibility\s+shim",
    "existing imports continue to work": r"existing imports continue to work",
    "backward-compatible keyword": r"backward-compatible",
    "_cast_enums method": r"_cast_enums",
    # plan 56 deprecated import paths
    "from agent.config import": r"from\s+agent\.config\s+import",
    "from mcp.github.service import": r"from\s+mcp\.github\.service\s+import",
    "from mcp.github import GitHubService": r"from\s+mcp\.github\s+import\s+GitHubService",
    # Workflow enforcement cleanup (plans 20260707-01 through 20260707-14)
    "workflow_mode field reference": r"workflow_mode\s*[=:]",
    "allow_startup_fallback call": r"\ballow_startup_fallback\b",
    "is_workflow_enabled call": r"\bis_workflow_enabled\b",
    "requires_startup_definition call": r"\brequires_startup_definition\b",
    "allow_turn_fallback call": r"\ballow_turn_fallback\b",
    "workflow_mode=disabled string": r'workflow_mode\s*=\s*["\']disabled["\']',
    "workflow_mode=auto string": r'workflow_mode\s*=\s*["\']auto["\']',
    "Workflow mode=disabled log": r"Workflow\s+mode=disabled",
    "direct LLM path phrase": r"direct\s+LLM\s+path",
    "direct-execution fallback phrase": r"direct.execution\s+fallback",
    "WorkflowExecutionPolicy import": r"from\s+agent\.workflow_execution_policy\s+import",
    "workflow_execution_policy module import": r"\bimport\s+workflow_execution_policy\b",
    "_reset_registry_for_testing": r"_reset_registry_for_testing",
}

# Patterns an Accepted ADR phrases as an explicit prohibition, keyed by name,
# each mapped to (adr_id, regex). Seeded only from a prohibition an
# implementer can point at verbatim in ADR text — not speculative rules (see
# docs/00_governance/governance_04_documentation-checks.md GV-012). Identifier-shaped
# (snake_case with underscores), not natural-language phrasing, so this does
# not also match the ADR's own prose describing the prohibition (e.g.
# ADR-001's Japanese "Workflow無効化モードを設けない" / "Workflowを迂回する
# 直接実行経路を設けない" text is not itself flagged).
ADR_PROHIBITED_PATTERNS: dict[str, tuple[str, str]] = {
    "workflow disable/bypass flag or function": (
        "ADR-001",
        r"\b(?:disable_workflow|workflow_disabled|bypass_workflow|skip_workflow)\b",
    ),
}

# ---------------------------------------------------------------------------
# Compatibility-exceptions manifest (replaces the former static DEFAULT_ALLOWLIST)
# ---------------------------------------------------------------------------
#
# The allowlist is now a data file (`tools/compat_exceptions.toml`) rather than
# an inline set: each entry carries an `id`, `owner`, `expires` review-by date,
# `removal_condition`, and `category` so CI can fail on an expired or incomplete
# exception instead of silently tolerating a stale path. `load_exceptions` reads
# it and `validate_exceptions` enforces the schema; both are exercised by
# tests/tools/test_check_compat_shims.py.

_VALID_CATEGORIES: frozenset[str] = frozenset(
    {"compatibility", "migration", "fallback", "fixture"}
)
_REQUIRED_FIELDS: tuple[str, ...] = (
    "id",
    "path",
    "reason",
    "owner",
    "expires",
    "removal_condition",
    "category",
)


def load_exceptions(
    manifest_path: Path,
) -> tuple[list[dict[str, str]], set[Path], frozenset[str]]:
    """Load the compatibility-exceptions manifest and resolve its paths.

    Returns ``(entries, allowlist, symbol_allowances)``: *entries* is the raw
    list of ``[[compatibility_exceptions]]`` tables (each a ``str``->``str``
    dict), *allowlist* is those entries' ``path`` values resolved against
    ``ROOT_DIR`` (so it matches the absolute paths ``main()`` scans, mirroring
    the old ``DEFAULT_ALLOWLIST``), and *symbol_allowances* is the set of names
    the report-only ``--check-doc-symbols`` stage must not flag. A missing
    ``path`` on an entry is tolerated here (it is reported by
    ``validate_exceptions``) so validation, not parsing, owns the error message.
    """
    data = tomllib.load(manifest_path.open("rb"))
    entries: list[dict[str, str]] = list(data.get("compatibility_exceptions", []))
    allowlist = {
        ROOT_DIR / e["path"] for e in entries if isinstance(e, dict) and e.get("path")
    }
    allowance_table = data.get("symbol_stage_allowance", {})
    symbol_allowances = frozenset(allowance_table.get("names", []))
    return entries, allowlist, symbol_allowances


def validate_exceptions(entries: list[dict[str, str]]) -> None:
    """Validate manifest entries; raise ``SystemExit(1)`` naming the first bad id.

    Enforces, per entry: all required fields present, a known ``category``, a
    parseable non-past ``expires`` ISO date, and a unique ``id``. Each defect is
    printed to stderr before raising, so CI reports exactly which id is at fault
    (REQ-002).
    """
    today = date.today()
    seen_ids: set[str] = set()
    for entry in entries:
        ident = entry.get("id", "<no id>")
        missing = [field for field in _REQUIRED_FIELDS if not entry.get(field)]
        if missing:
            print(
                f"invalid compatibility exception {ident!r}: missing fields {missing}",
                file=sys.stderr,
            )
            sys.exit(1)
        category = entry["category"]
        if category not in _VALID_CATEGORIES:
            print(
                f"invalid compatibility exception {ident!r}: unknown category "
                f"{category!r} (expected one of {sorted(_VALID_CATEGORIES)})",
                file=sys.stderr,
            )
            sys.exit(1)
        try:
            expires = date.fromisoformat(entry["expires"])
        except ValueError:
            print(
                f"invalid compatibility exception {ident!r}: unparseable expires "
                f"{entry['expires']!r} (expected an ISO date)",
                file=sys.stderr,
            )
            sys.exit(1)
        if expires < today:
            print(
                f"invalid compatibility exception {ident!r}: expires "
                f"{expires.isoformat()} is in the past",
                file=sys.stderr,
            )
            sys.exit(1)
        if ident in seen_ids:
            print(
                f"invalid compatibility exception {ident!r}: duplicate id",
                file=sys.stderr,
            )
            sys.exit(1)
        seen_ids.add(ident)


# Names defined under tools/ that `check_function_references` never scans (that
# helper covers scripts/ only), so the symbol stage must drop them itself.
_TOOL_DEF_RE = re.compile(
    r"^\s*(?:async\s+)?def\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\(", re.MULTILINE
)
_TOOL_CLASS_RE = re.compile(r"^\s*class\s+([a-zA-Z_][a-zA-Z0-9_]*)", re.MULTILINE)
# Matches the backticked `name()` token embedded in a library Issue message so
# the post-filter can key off the referenced symbol.
_MESSAGE_NAME_RE = re.compile(r"`([a-zA-Z_]\w*)\(\)`")


def check_doc_symbols(
    repo_root: Path,
    docs_dir: Path,
    symbol_allowances: frozenset[str],
) -> list[Issue]:
    """Warn about `func()` refs in docs with no def under scripts/.

    Reuses `tools/_docs_consistency_lib.check_function_references`, then drops
    (a) names defined under tools/ (never scanned by that helper) and (b) the
    manifest's symbol-stage allowances. Returns the remaining WARNING Issues;
    main() prints them and counts each one toward the exit code.
    """
    from tools._docs_consistency_lib import (
        check_function_references,
        discover_md_files,
    )

    defined_under_tools: set[str] = set()
    tools_dir = repo_root / "tools"
    if tools_dir.is_dir():
        for py_file in tools_dir.rglob("*.py"):
            text = py_file.read_text(encoding="utf-8")
            defined_under_tools.update(_TOOL_DEF_RE.findall(text))
            defined_under_tools.update(_TOOL_CLASS_RE.findall(text))

    not_flagged = defined_under_tools | set(symbol_allowances)
    issues = check_function_references(
        docs_dir, discover_md_files(docs_dir, prefix=""), repo_root
    )
    return [
        issue
        for issue in issues
        if (match := _MESSAGE_NAME_RE.search(issue.message)) is None
        or match.group(1) not in not_flagged
    ]


# ---------------------------------------------------------------------------
# Check: removed-name reintroduction in current specifications (docs/ only)
# ---------------------------------------------------------------------------
#
# `plans/20260903-090945_plan.md` (compatterms) REQ-003 designs an asymmetric
# rule: a name confirmed fully absent from source needs only a simple
# grep-vs-source-absence check (implemented here); a name that remains in
# source but is no longer the current production path (for example a function
# that is still defined but superseded)
# needs a harder, context-aware "is this presented as current?" check that
# this function does not attempt — see that Plan's Design section for why the
# two cases are not the same check. Scoped to docs/ only (this checks
# documentation claims, not source code, which is where check_compat_patterns
# above already looks for the removed identifiers themselves).

_HISTORICAL_CONTEXT_MARKERS: frozenset[str] = frozenset(
    {
        "legacy",
        "historical",
        "archive only",
        "resolved",
        "was:",
        "removed",
        # Japanese equivalents — this repository's docs mix English and
        # Japanese prose, and the English-only marker set above previously
        # produced false positives on Japanese-language historical/resolved
        # notes (found while extending _REMOVED_NAME_PATTERNS below).
        "解消",
        "解決",
        "廃止",
        "撤廃",
        "削除済み",
        "確認済み",
    }
)


def _removed_slash_command(name: str) -> re.Pattern[str]:
    r"""Compile a removed slash-command pattern that matches ONLY the command
    form, never a path or filename substring.

    GV-017's four removed names (`/diff`, `/system`, `/audit`, `/workflow`) were
    previously matched with `/<name>\b`, which also matched inside file paths
    (`scripts/mcp_servers/audit.py`), filenames (`<log_dir>/audit.log`,
    `dict/system.dic`), and path segments (`Routing/audit/Config`,
    `agent/workflow/`). The leading `(?<!\w)` requires the `/` to begin a token
    rather than continue a path; the trailing `(?![\w/])(?!\.\w)` rejects a
    following path separator, identifier character, or file extension while
    still allowing a sentence-ending period.
    """
    return re.compile(rf"(?<!\w)/{name}(?![\w/])(?!\.\w)")


_REMOVED_NAME_PATTERNS: dict[str, re.Pattern[str]] = {
    "_update_null_fill (confirmed removed from scripts/rag/ingestion/, per "
    "plans/20260903-085718_plan.md)": re.compile(r"_update_null_fill\b"),
    "SecurityProfile.LOCAL (confirmed removed, per "
    "plans/done/20260903-091417_plan.md — localremoval)": re.compile(
        r"SecurityProfile\.LOCAL\b|security_profile\s*=\s*[\"']local[\"']"
    ),
    "allow_public_bind (confirmed removed, per "
    "plans/done/20260903-091921_plan.md — loopbackonly)": re.compile(
        r"\ballow_public_bind\b"
    ),
    "empty auth_token permitted (confirmed removed — mandatory MCP "
    "authentication, per plans/done/20260903-092407_plan.md — mcpauth)": re.compile(
        r"auth_token(?:_env)?\s*=\s*[\"']{2}|empty\s+auth_token"
    ),
    "shared/security package (confirmed removed — SHARED-001 resolution)": re.compile(
        r"\bHighRiskToolPolicy\b|\bSecurityMode\b|\bAuditLogger\b|shared[./]security\b"
    ),
    "LlmRetryHandler/llm_max_retries/stat_retries (confirmed removed — "
    "test-only LLM retry path)": re.compile(
        r"\bLlmRetryHandler\b|\bllm_max_retries\b|\bstat_retries\b|\bLLMClient\.request_with_retry\b"
    ),
    "validate_all_routing (confirmed removed — SHARED-002 resolution)": re.compile(
        r"\bvalidate_all_routing\b"
    ),
    "is_side_effect (confirmed removed — SHARED-002 resolution)": re.compile(
        r"\bis_side_effect\b"
    ),
    "ToolResultCache/CacheEntry (confirmed removed — SHARED-002 resolution)": re.compile(
        r"\bToolResultCache\b|\bCacheEntry\b"
    ),
    "LLMClient.call (confirmed removed — SHARED-002 resolution)": re.compile(
        r"\bLLMClient\.call\("
    ),
    "SQLiteSessionStore/SessionStore (confirmed removed — SHARED-002 resolution)": re.compile(
        r"\bSQLiteSessionStore\b|\bSessionStore\b"
    ),
    "/diff (confirmed removed, per plans/20261016-233542_plan.md — diffcmd)": _removed_slash_command(
        "diff"
    ),
    "/system (confirmed removed, per plans/20261016-233542_plan.md — syscmd)": _removed_slash_command(
        "system"
    ),
    "/audit (confirmed removed, per plans/20261016-233542_plan.md — auditcmd)": _removed_slash_command(
        "audit"
    ),
    "/workflow (confirmed removed, per plans/20261016-233542_plan.md — wfcmd)": _removed_slash_command(
        "workflow"
    ),
    "security_lockdown_enabled (confirmed removed — the deny-all suppression knob lost its "
    "only consumer when agent/services/security_audit.py was deleted, per "
    "plans/done/20261015-112526_plan.md REQ-017; ADR-004 leaves no configuration path that "
    "downgrades a Safety/Integrity posture failure)": re.compile(
        r"\bsecurity_lockdown_enabled\b"
    ),
}

_TOOL_ROUTE_RESOLVER_RE = re.compile(r"\bToolRouteResolver\b")
_SERVER_CONFIGS_RE = re.compile(r"\bserver_configs\b")
# A `server_configs` mention that DENIES the stale resolver argument
# ("no server_configs parameter", "server_configs does not exist") documents
# the absence rather than reintroducing the claim, so it must not be flagged.
# Exempt such lines to avoid false-positives on the corrections made by
# plans/20260903-090104_plan.md.
_NEGATED_SERVER_CONFIGS_RE = re.compile(
    r"\bno\b[^.\n]*\bserver_configs\b"
    r"|\bserver_configs\b[^.\n]*(?:does not|has no|never)\b",
    re.IGNORECASE,
)
_HEADING_RE = re.compile(r"^#{1,6}\s")


def _is_historical_context(lines: list[str], line_idx: int) -> bool:
    """True if *line_idx* itself, or any of the preceding 10 lines, carries an
    explicit historical/resolved marker — mirrors
    tools/check_docs_quality.py's `_is_historical_context` helper so both
    tools recognize "this is a historical reference, not a current claim" the
    same way."""
    start = max(0, line_idx - 10)
    for i in range(start, line_idx + 1):
        if any(marker in lines[i].lower() for marker in _HISTORICAL_CONTEXT_MARKERS):
            return True
    return False


_MCP_HEALTH_REEXPORT_NAMES = frozenset(
    {
        "McpServerHealthRegistry",
        "McpServerHealthState",
        "MCPHealthSnapshot",  # pre-rename name
        "ServerHealthState",  # pre-rename name
        "classify_server_failure",  # pre-rename name
    }
)


def check_mcp_health_reexport_import(content: str, filepath: Path) -> list[str]:
    """Flag an import of a Health name from the removed shared.mcp_config re-export."""
    if filepath.suffix != ".py":
        return []
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []
    issues: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "shared.mcp_config":
            for alias in node.names:
                if alias.name in _MCP_HEALTH_REEXPORT_NAMES:
                    issues.append(
                        f"{filepath}:{node.lineno}: Health name imported from the "
                        f"removed shared.mcp_config re-export path — import "
                        f"'{alias.name}' from shared.mcp_health instead"
                    )
    return issues


def check_gateless_discovery_construction(content: str, filepath: Path) -> list[str]:
    """Flag a McpToolDiscoveryService construction that omits posture_gates."""
    if filepath.suffix != ".py":
        return []
    try:
        tree = ast.parse(content)
    except SyntaxError:
        return []
    issues: list[str] = []
    for node in ast.walk(tree):
        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "McpToolDiscoveryService"
            and "posture_gates" not in {kw.arg for kw in node.keywords if kw.arg}
            and len(node.args) < 2
        ):
            issues.append(
                f"{filepath}:{node.lineno}: McpToolDiscoveryService constructed "
                f"without posture_gates — the argument is required (no None default)"
            )
    return issues


def check_removed_name_reintroduction(content: str, filepath: Path) -> list[str]:
    """Flag a removed name presented as current outside historical context.

    Only applies to `*.md` files — this checks whether documentation
    reintroduces a claim about a name confirmed absent from source, not
    whether the name itself appears in source (that's `check_compat_patterns`'s
    job for source files). Not restricted to files physically under this
    repository's `docs/` directory, so it can be exercised against isolated
    fixtures in tests, not only real files on disk.
    """
    if filepath.suffix != ".md":
        return []

    issues: list[str] = []
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if _is_historical_context(lines, i):
            continue
        for description, pattern in _REMOVED_NAME_PATTERNS.items():
            if pattern.search(line):
                issues.append(
                    f"{filepath}:{i + 1}: removed name reintroduced as current — "
                    f"{description}: {line.strip()}"
                )

    # ToolRouteResolver+server_configs: section-scoped, not line-adjacent —
    # a `## <Heading>` mentioning ToolRouteResolver may describe its
    # constructor's arguments (including the stale server_configs claim)
    # several bullets below the heading itself, with no repeated mention of
    # the class name on that specific line.
    section_start = 0
    for i in range(len(lines) + 1):
        at_boundary = i == len(lines) or _HEADING_RE.match(lines[i])
        if not at_boundary:
            continue
        section = lines[section_start:i]
        if (
            section
            and _TOOL_ROUTE_RESOLVER_RE.search("\n".join(section))
            and _SERVER_CONFIGS_RE.search("\n".join(section))
        ):
            for j, sec_line in enumerate(section):
                if not _SERVER_CONFIGS_RE.search(sec_line):
                    continue
                if _is_historical_context(lines, section_start + j):
                    continue
                if _NEGATED_SERVER_CONFIGS_RE.search(sec_line):
                    continue
                issues.append(
                    f"{filepath}:{section_start + j + 1}: "
                    f"ToolRouteResolver+server_configs co-occurrence in the "
                    f"same section — this constructor argument does not "
                    f"exist in current code (confirmed removed, per "
                    f"plans/20260903-090104_plan.md): {sec_line.strip()}"
                )
        section_start = i
    return issues


def is_allowlisted(filepath: Path, allowlist: set[Path]) -> bool:
    """Check if the file is in the allowlist."""
    return filepath in allowlist


def check_compat_patterns(
    content: str, filepath: Path, allowlist: set[Path]
) -> list[str]:
    """Check for backward compatibility leftovers in content."""
    issues: list[str] = []
    if is_allowlisted(filepath, allowlist):
        return issues

    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        for pattern_name, pattern in COMPAT_PATTERNS.items():
            if re.search(pattern, stripped):
                issues.append(
                    f"{filepath}:{i}: backward compatibility leftover — '{pattern_name}': {stripped}"
                )
    return issues


def check_adr_prohibited_patterns(
    content: str, filepath: Path, allowlist: set[Path]
) -> list[str]:
    """Check for patterns an Accepted ADR explicitly prohibits."""
    issues: list[str] = []
    if is_allowlisted(filepath, allowlist):
        return issues

    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        stripped = line.strip()
        for pattern_name, (adr_id, pattern) in ADR_PROHIBITED_PATTERNS.items():
            if re.search(pattern, stripped):
                issues.append(
                    f"{filepath}:{i}: {adr_id} prohibited pattern — '{pattern_name}': {stripped}"
                )
    return issues


def check_all(
    content: str,
    filepath: Path,
    allowlist: set[Path],
    include_removed_names: bool = False,
) -> list[str]:
    """Run all checks and return combined issues.

    `include_removed_names` defaults to `False` so this tool's existing
    default invocation (a bare `python -m tools.check_compat_shims` with no
    flags) keeps its current pass/fail behavior unchanged; CI and pre-commit
    pass `--check-removed-names` explicitly.
    `check_removed_name_reintroduction()` reports zero findings in the live
    corpus today: the section-scoped `ToolRouteResolver`+`server_configs`
    matcher was tightened to exempt lines that deny the stale argument
    (the corrections made by `plans/20260903-090104_plan.md`). The
    check is opt-in via the flag and blocking wherever the flag is passed
    (CI and pre-commit).

    Two syntax-tree rules are always on: a Health-name import from the removed
    `shared.mcp_config` re-export, and a `McpToolDiscoveryService` construction
    without `posture_gates`.
    """
    if is_allowlisted(filepath, allowlist):
        return []
    issues = check_compat_patterns(
        content, filepath, allowlist
    ) + check_adr_prohibited_patterns(content, filepath, allowlist)
    issues += check_mcp_health_reexport_import(content, filepath)
    issues += check_gateless_discovery_construction(content, filepath)
    if include_removed_names:
        issues += check_removed_name_reintroduction(content, filepath)
    return issues


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Check for backward compatibility leftovers in source code and docs"
    )
    parser.add_argument(
        "--allowlist",
        type=Path,
        default=None,
        help="Override the default allowlist with a custom file (one path per line)",
    )
    parser.add_argument(
        "--check-removed-names",
        action="store_true",
        help=(
            "Also run the removed-name-reintroduction check (docs/*.md only; "
            "see check_removed_name_reintroduction()). Off by default — the "
            "live corpus reports zero findings (the ToolRouteResolver+"
            "server_configs matcher exempts lines that deny the stale "
            "argument); CI and pre-commit pass this flag, so a finding blocks."
        ),
    )
    parser.add_argument(
        "--check-doc-symbols",
        action="store_true",
        help=(
            "Fail on backtick-quoted function references in docs/ with no "
            "matching definition under scripts/ (reuses "
            "check_function_references; each finding counts toward the exit code)."
        ),
    )
    parser.add_argument(
        "files",
        nargs="*",
        help="Files to check (default: scripts/, docs/, tests/, tools/)",
    )
    args = parser.parse_args()

    # Load allowlist
    if args.allowlist and args.allowlist.exists():
        allowlist = {
            Path(p.strip())
            for p in args.allowlist.read_text().splitlines()
            if p.strip()
        }
        symbol_allowances: frozenset[str] = frozenset()
    else:
        entries, allowlist, symbol_allowances = load_exceptions(
            ROOT_DIR / "tools" / "compat_exceptions.toml"
        )
        validate_exceptions(entries)  # exits 1 on an expired/incomplete entry

    # Determine files to check
    if not args.files:
        dirs_to_scan = [
            ROOT_DIR / "scripts",
            ROOT_DIR / "docs",
            ROOT_DIR / "tests",
            ROOT_DIR / "tools",
        ]
        files: list[Path] = []
        for d in dirs_to_scan:
            if d.exists():
                files.extend(d.glob("**/*.py"))
                files.extend(d.glob("**/*.md"))
        files = sorted(set(files))  # Deduplicate
    else:
        files = []
        for f in args.files:
            p = Path(f).resolve()
            if p.is_dir():
                files.extend(p.glob("**/*.py"))
                files.extend(p.glob("**/*.md"))
            else:
                files.append(p)
        files = sorted(set(files))

    # Symbol stage: the live corpus has zero findings, so each remaining
    # finding is blocking.
    total_issues = 0
    if args.check_doc_symbols:
        symbol_warnings = check_doc_symbols(
            ROOT_DIR, ROOT_DIR / "docs", symbol_allowances
        )
        for warning in symbol_warnings:
            print(
                f"[WARNING] {warning.file}:{warning.line_no}: {warning.message}",
                file=sys.stderr,
            )
        total_issues += len(symbol_warnings)

    for filepath in files:
        if not filepath.exists():
            continue
        content = filepath.read_text(encoding="utf-8")
        issues = check_all(
            content, filepath, allowlist, include_removed_names=args.check_removed_names
        )
        if issues:
            total_issues += len(issues)
            try:
                display_path = filepath.relative_to(ROOT_DIR)
            except ValueError:
                display_path = filepath
            print(f"\n--- {display_path} ---", file=sys.stderr)
            for issue in issues:
                print(issue, file=sys.stderr)

    if total_issues > 0:
        print(f"\n{total_issues} issue(s) found", file=sys.stderr)
        return 1
    print("All checks passed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
