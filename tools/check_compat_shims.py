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
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

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
# docs/00_governance_04_documentation-checks.md GV-014). Identifier-shaped
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

# Allowlist: files that are permitted to contain these patterns (archive/migration notes only)
DEFAULT_ALLOWLIST = {
    # Migration notes that document historical changes
    ROOT_DIR / "docs" / "03_rag_00_document-guide.md",  # documents removed rag.llm stub
    # Test file intentionally referencing the removed re-export stub
    ROOT_DIR / "tests" / "agent" / "test_rag_get_cfg.py",
    # Test files with assertions about absence of removed compatibility patterns
    ROOT_DIR / "tests" / "shared" / "test_route_resolver.py",
    ROOT_DIR / "tests" / "mcp_servers" / "rag_pipeline" / "test_mcp_rag_pipeline.py",
    ROOT_DIR
    / "tests"
    / "mcp_servers"
    / "rag_pipeline"
    / "test_rag_pipeline_mcp_service.py",
    # Test file with description mentioning static fallback as a concept
    ROOT_DIR / "tests" / "shared" / "test_rag_tools_consistency.py",
    # Tests intentionally referencing removed commands
    ROOT_DIR / "tests" / "agent" / "commands" / "test_cmd_registry_note_removal.py",
    ROOT_DIR / "tests" / "agent" / "commands" / "test_removed_commands.py",
    ROOT_DIR / "tests" / "db" / "test_create_schema.py",
    # Docs documenting removed features (POST /v1/search, /mcp install, /note, /db aliases)
    ROOT_DIR / "docs" / "04_mcp_00_document-guide.md",
    ROOT_DIR / "docs" / "05_agent_90_inconsistencies_and_known_issues.md",
    # Migration notes doc (split from the former 05_agent_07_cli-and-commands.md) documenting removed /note and /db aliases
    ROOT_DIR / "docs" / "05_agent_07_07_cli-and-commands-migration-notes.md",
    # Doc documenting verification task for deleted commands
    ROOT_DIR / "docs" / "05_agent_00_document-guide.md",
    # Docs documenting deleted source files (07_ref-sqlite.md, 07_spec_db.md) and stale issue IDs (DESIGN-01/02)
    ROOT_DIR / "docs" / "90_shared_00_document-guide.md",
    # Doc (split from the former 90_shared_04_db_architecture_and_schema.md) documenting the deleted workflow_schema.py entry point
    ROOT_DIR
    / "docs"
    / "90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md",
    # Doc recording removed direct-execution-fallback behavior as a deprecated item
    ROOT_DIR / "docs" / "00_governance_05_deprecated-items.md",
    # Doc explicitly stating the absence of a compatibility shim (negation, not a leftover)
    ROOT_DIR / "docs" / "04_mcp_03_06_tool-runtime-availability-metadata.md",
    # ADR documenting verification of deprecated items (similar purpose to deprecated-items.md)
    ROOT_DIR / "docs" / "adr_task15_summary.md",
    # ADR documenting verification of deprecated items
    ROOT_DIR / "docs" / "adr_verification_matrix.md",
    # Test files using the test-only _reset_registry_for_testing helper as intended (not production misuse)
    ROOT_DIR / "tests" / "conftest.py",
    ROOT_DIR / "tests" / "agent" / "services" / "test_mcp_tool_discovery.py",
    ROOT_DIR / "tests" / "agent" / "test_startup_routing_drift.py",
    ROOT_DIR / "tests" / "shared" / "test_tool_registry.py",
    ROOT_DIR / "tests" / "shared" / "test_tool_registry_counts.py",
    # CI guard test that references the helper name as a string to assert its absence from production code
    ROOT_DIR / "tests" / "shared" / "test_tool_registry_reset_protection.py",
    # plan 56 patterns — test file that checks the checker itself (contains patterns as test data)
    ROOT_DIR / "tests" / "tools" / "test_check_compat_shims.py",
    # The checker itself (self-reference for new location)
    ROOT_DIR / "tools" / "check_compat_shims.py",
    # Test file that verifies _MCP_TOOLS is absent (contains the pattern as a check target)
    ROOT_DIR / "tests" / "mcp_servers" / "test_mcp_tool_schema_exports.py",
    # Doc that documents the _MCP_TOOLS → TOOL_LIST migration policy
    ROOT_DIR / "docs" / "04_mcp_07_tool_schema_export_policy.md",
    # Definition site of test-only reset helper (not a misuse)
    ROOT_DIR / "scripts" / "shared" / "tool_registry.py",
}


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


def check_all(content: str, filepath: Path, allowlist: set[Path]) -> list[str]:
    """Run all checks and return combined issues."""
    return check_compat_patterns(
        content, filepath, allowlist
    ) + check_adr_prohibited_patterns(content, filepath, allowlist)


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
    else:
        allowlist = DEFAULT_ALLOWLIST.copy()

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

    total_issues = 0
    for filepath in files:
        if not filepath.exists():
            continue
        content = filepath.read_text(encoding="utf-8")
        issues = check_all(content, filepath, allowlist)
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
