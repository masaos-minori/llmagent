#!/usr/bin/env python3
"""tools/check_suppression_justification.py

CI check for suppression-comment governance in `scripts/` and `tests/`:
`# noqa`, `# type: ignore`, and `# nosec` each require a rule/error code AND an
em-dash (U+2014, surrounded by spaces) delimited justification following it.
See `rules/coding.md` §Suppression governance.

Usage:
    python -m tools.check_suppression_justification [--allowlist <path>] [files...]
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent.parent

EM_DASH = "—"

# One pattern per suppression kind. Each optionally captures a trailing rule/error
# code (group "code") so callers can tell "no code" apart from "code, no justification".
SUPPRESSION_PATTERNS: dict[str, re.Pattern[str]] = {
    "noqa": re.compile(
        r"#\s*noqa\b(?::\s*(?P<code>[A-Za-z0-9]+(?:[,\s]+[A-Za-z0-9]+)*))?"
    ),
    "type: ignore": re.compile(r"#\s*type:\s*ignore\b(?:\[(?P<code>[^\]]*)\])?"),
    "nosec": re.compile(
        r"#\s*nosec\b(?:\s+(?P<code>[A-Za-z0-9]+(?:[,\s]+[A-Za-z0-9]+)*))?"
    ),
}

# Allowlist: files with pre-existing suppression comments that lack a code and/or
# em-dash justification, grandfathered so only new/modified violations fail the check.
DEFAULT_ALLOWLIST = {
    ROOT_DIR / "scripts" / "agent" / "commands" / "cmd_config.py",
    ROOT_DIR / "scripts" / "agent" / "commands" / "cmd_memory.py",
    ROOT_DIR / "scripts" / "agent" / "commands" / "registry.py",
    ROOT_DIR / "scripts" / "agent" / "commands" / "session_title.py",
    ROOT_DIR / "scripts" / "agent" / "http_lifecycle.py",
    ROOT_DIR / "scripts" / "agent" / "memory" / "fts_query.py",
    ROOT_DIR / "scripts" / "agent" / "orchestrator.py",
    ROOT_DIR / "scripts" / "agent" / "repl_health.py",
    ROOT_DIR / "scripts" / "agent" / "services" / "mcp_status.py",
    ROOT_DIR / "scripts" / "agent" / "services" / "mcp_tool_discovery.py",
    ROOT_DIR / "scripts" / "agent" / "tool_runner.py",
    ROOT_DIR / "scripts" / "db" / "helper.py",
    ROOT_DIR / "scripts" / "eventbus" / "ack_route.py",
    ROOT_DIR / "scripts" / "eventbus" / "app.py",
    ROOT_DIR / "scripts" / "eventbus" / "route_helpers.py",
    ROOT_DIR / "scripts" / "eventbus" / "subscribe_route.py",
    ROOT_DIR / "scripts" / "mcp_servers" / "cicd" / "exception_handlers.py",
    ROOT_DIR / "scripts" / "mcp_servers" / "cicd" / "service_business.py",
    ROOT_DIR
    / "scripts"
    / "mcp_servers"
    / "cicd"
    / "service_github_actions_composite.py",
    ROOT_DIR / "scripts" / "mcp_servers" / "cicd" / "service_init.py",
    ROOT_DIR / "scripts" / "mcp_servers" / "git" / "git_tools.py",
    ROOT_DIR / "scripts" / "mcp_servers" / "github" / "github_server.py",
    ROOT_DIR / "scripts" / "mcp_servers" / "github" / "server_common.py",
    ROOT_DIR / "scripts" / "mcp_servers" / "github" / "service_business.py",
    ROOT_DIR / "scripts" / "mcp_servers" / "github" / "service_file.py",
    ROOT_DIR / "scripts" / "mcp_servers" / "github" / "service_init.py",
    ROOT_DIR / "scripts" / "mcp_servers" / "github" / "service_issues.py",
    ROOT_DIR / "scripts" / "mcp_servers" / "github" / "service_pull_requests.py",
    ROOT_DIR / "scripts" / "mcp_servers" / "github" / "service_repository.py",
    ROOT_DIR / "scripts" / "mcp_servers" / "github" / "service_security.py",
    ROOT_DIR / "scripts" / "mcp_servers" / "mdq" / "indexer.py",
    ROOT_DIR / "scripts" / "rag" / "http_augment.py",
    ROOT_DIR / "scripts" / "rag" / "ingestion" / "pipeline_utils.py",
    ROOT_DIR / "scripts" / "rag" / "repository.py",
    ROOT_DIR / "scripts" / "shared" / "mcp_config.py",
    ROOT_DIR / "scripts" / "shared" / "otel_tracer.py",
    ROOT_DIR / "scripts" / "shared" / "tool_executor.py",
    ROOT_DIR / "tests" / "agent" / "commands" / "test_agent_cmd_memory.py",
    ROOT_DIR / "tests" / "agent" / "commands" / "test_agent_cmd_session.py",
    ROOT_DIR / "tests" / "agent" / "commands" / "test_agent_rag.py",
    ROOT_DIR / "tests" / "agent" / "commands" / "test_cmd_audit.py",
    ROOT_DIR / "tests" / "agent" / "commands" / "test_cmd_context_refactor.py",
    ROOT_DIR / "tests" / "agent" / "commands" / "test_cmd_mcp.py",
    ROOT_DIR / "tests" / "agent" / "commands" / "test_cmd_registry_note_removal.py",
    ROOT_DIR / "tests" / "agent" / "memory" / "test_jsonl_store.py",
    ROOT_DIR / "tests" / "agent" / "memory" / "test_memory_docs_examples.py",
    ROOT_DIR / "tests" / "agent" / "memory" / "test_memory_layer.py",
    ROOT_DIR / "tests" / "agent" / "memory" / "test_memory_store.py",
    ROOT_DIR / "tests" / "agent" / "services" / "test_config_reload.py",
    ROOT_DIR / "tests" / "agent" / "shared" / "test_mcp_health_interpretation.py",
    ROOT_DIR / "tests" / "agent" / "test_agent_session.py",
    ROOT_DIR / "tests" / "agent" / "test_cli_view.py",
    ROOT_DIR / "tests" / "agent" / "test_config_dataclasses.py",
    ROOT_DIR / "tests" / "agent" / "test_diagnostic_store.py",
    ROOT_DIR / "tests" / "agent" / "test_http_lifecycle_command_validator.py",
    ROOT_DIR / "tests" / "agent" / "test_http_lifecycle_integration.py",
    ROOT_DIR / "tests" / "agent" / "test_http_lifecycle_process_terminator.py",
    ROOT_DIR / "tests" / "agent" / "test_llm_client.py",
    ROOT_DIR / "tests" / "agent" / "test_llm_partial_completion.py",
    ROOT_DIR / "tests" / "agent" / "test_memory_local_only.py",
    ROOT_DIR / "tests" / "agent" / "test_message_schema.py",
    ROOT_DIR / "tests" / "agent" / "test_orchestrator.py",
    ROOT_DIR / "tests" / "agent" / "test_repl.py",
    ROOT_DIR / "tests" / "db" / "test_db_maintenance.py",
    ROOT_DIR / "tests" / "db" / "test_db_public_api.py",
    ROOT_DIR / "tests" / "db" / "test_db_store_impl.py",
    ROOT_DIR / "tests" / "db" / "test_rag_consistency.py",
    ROOT_DIR / "tests" / "eventbus" / "test_eventbus_health.py",
    ROOT_DIR / "tests" / "eventbus" / "test_eventbus_publish.py",
    ROOT_DIR / "tests" / "eventbus" / "test_eventbus_replay_subscribe.py",
    ROOT_DIR / "tests" / "eventbus_helpers.py",
    ROOT_DIR / "tests" / "integration" / "test_rag_llm_integration.py",
    ROOT_DIR / "tests" / "mcp_servers" / "cicd" / "test_mcp_server_health_status.py",
    ROOT_DIR / "tests" / "mcp_servers" / "file" / "test_file_write_mcp_service.py",
    ROOT_DIR / "tests" / "mcp_servers" / "mdq" / "test_mdq_get_chunk_behavior.py",
    ROOT_DIR / "tests" / "mcp_servers" / "mdq" / "test_mdq_incremental_refresh.py",
    ROOT_DIR / "tests" / "mcp_servers" / "mdq" / "test_mdq_index_serialization.py",
    ROOT_DIR / "tests" / "mcp_servers" / "mdq" / "test_mdq_search_modes.py",
    ROOT_DIR / "tests" / "mcp_servers" / "mdq" / "test_mdq_service.py",
    ROOT_DIR / "tests" / "mcp_servers" / "test_mcp_dispatch.py",
    ROOT_DIR / "tests" / "rag" / "ingestion" / "test_ingester.py",
    ROOT_DIR / "tests" / "rag" / "ingestion" / "test_ingestion_freshness.py",
    ROOT_DIR / "tests" / "rag" / "ingestion" / "test_rag_ingester.py",
    ROOT_DIR / "tests" / "rag" / "test_rag_pipeline_stage.py",
    ROOT_DIR / "tests" / "shared" / "test_config_loader.py",
    ROOT_DIR / "tests" / "shared" / "test_llm_reconnect.py",
    ROOT_DIR / "tests" / "shared" / "test_llm_sse_stream.py",
    ROOT_DIR / "tests" / "shared" / "test_logger.py",
    ROOT_DIR / "tests" / "shared" / "test_mcp_config_validation.py",
    ROOT_DIR / "tests" / "shared" / "test_runtime_tool.py",
    ROOT_DIR / "tests" / "shared" / "test_tool_executor.py",
    ROOT_DIR / "tests" / "shared" / "test_tool_executor_stampede.py",
    ROOT_DIR / "tests" / "shared" / "test_tool_transport_invoker.py",
    ROOT_DIR / "tests" / "tools" / "test_check_suppression_justification.py",
}


def is_allowlisted(filepath: Path, allowlist: set[Path]) -> bool:
    """Check if the file is in the allowlist."""
    return filepath in allowlist


def _is_justified(remainder: str) -> bool:
    """Check whether an em-dash-delimited justification follows a suppression marker."""
    return f" {EM_DASH} " in remainder


def check_suppression_justification(
    content: str, filepath: Path, allowlist: set[Path]
) -> list[str]:
    """Check for unjustified `# noqa` / `# type: ignore` / `# nosec` comments."""
    issues: list[str] = []
    if is_allowlisted(filepath, allowlist):
        return issues

    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        for kind_name, pattern in SUPPRESSION_PATTERNS.items():
            for match in pattern.finditer(line):
                code = match.groupdict().get("code")
                has_code = bool(code and code.strip())
                remainder = line[match.end() :]
                has_justification = _is_justified(remainder)
                if not (has_code and has_justification):
                    issues.append(
                        f"{filepath}:{i}: unjustified '{kind_name}' suppression "
                        f"(missing {'code' if not has_code else 'em-dash justification'}): "
                        f"{line.strip()}"
                    )
    return issues


def check_all(content: str, filepath: Path, allowlist: set[Path]) -> list[str]:
    """Run all checks and return combined issues."""
    return check_suppression_justification(content, filepath, allowlist)


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Check that '# noqa', '# type: ignore', and '# nosec' comments carry a "
            "rule/error code and an em-dash-delimited justification"
        )
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
        help="Files to check (default: scripts/, tests/)",
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
            ROOT_DIR / "tests",
        ]
        files: list[Path] = []
        for d in dirs_to_scan:
            if d.exists():
                files.extend(d.glob("**/*.py"))
        files = sorted(set(files))  # Deduplicate
    else:
        files = [Path(f) for f in args.files]

    total_issues = 0
    for filepath in files:
        if not filepath.exists():
            continue
        content = filepath.read_text(encoding="utf-8")
        issues = check_all(content, filepath, allowlist)
        if issues:
            total_issues += len(issues)
            print(f"\n--- {filepath.relative_to(ROOT_DIR)} ---", file=sys.stderr)
            for issue in issues:
                print(issue, file=sys.stderr)

    if total_issues > 0:
        print(f"\n{total_issues} issue(s) found", file=sys.stderr)
        return 1
    print("All checks passed", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
