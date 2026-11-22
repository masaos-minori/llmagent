#!/usr/bin/env python3
"""scripts/shared/tool_constants.py — Reference-data frozensets for MCP tool names (agentcfg003, REQ-007).

Reference-data frozensets for MCP tool names (agentcfg003, REQ-007).

These sets are reference data for drift detection and tests only: they give the
drift checks something to compare a tool's declared metadata against. No runtime
decision reads them. Runtime decisions read the declared fields carried by each
`RuntimeTool` (`is_write`, `side_effect_class`, `retry_policy`,
`agent_safety_tier`, ...), built by `shared.runtime_tool.build_runtime_tool()`
from the producers' declarations.

Per-consumer status:
  - registry seed: a one-time import-time seed for ToolRegistry, not a fallback.
  - routing and scheduling: driven only by live `/v1/tools` discovery
    (RuntimeToolRegistry) and ToolSpec fields resolved from it
    (agent/tool_scheduler.py::build_execution_groups()), not these sets.
  - risk classification and retry classification: driven by the declared fields;
    these sets only report drift against the declarations.
Centralised here to avoid silent drift when tool lists change.
All sets are frozensets; treat them as read-only.
"""

from __future__ import annotations

READ_TOOLS: frozenset[str] = frozenset(
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
    },
)

WRITE_TOOLS: frozenset[str] = frozenset(
    {
        "write_file",
        "edit_file",
        "create_directory",
        "move_file",
    },
)

DELETE_TOOLS: frozenset[str] = frozenset(
    {
        "delete_file",
        "delete_directory",
    },
)

RAG_READ_TOOLS: frozenset[str] = frozenset(
    {
        "rag_run_pipeline",
        "rag_debug_pipeline",
        "rag_list_documents",
    },
)

RAG_WRITE_TOOLS: frozenset[str] = frozenset({"rag_delete_document"})

RAG_TOOLS: frozenset[str] = RAG_READ_TOOLS | RAG_WRITE_TOOLS

CICD_READ_TOOLS: frozenset[str] = frozenset(
    {
        "get_workflow_runs",
        "get_workflow_status",
        "get_workflow_logs",
    },
)

CICD_WRITE_TOOLS: frozenset[str] = frozenset({"trigger_workflow"})

CICD_TOOLS: frozenset[str] = CICD_READ_TOOLS | CICD_WRITE_TOOLS

# Markdown Context Compression Engine tools
# Reviewed for TOOLS/READ/WRITE unification (see plan 20260813-192143); intentionally left as a
# two-set group — no MDQ_READ_TOOLS exists.
MDQ_TOOLS: frozenset[str] = frozenset(
    {
        "search_docs",
        "get_chunk",
        "outline",
        "index_paths",
        "refresh_index",
        "stats",
        "grep_docs",
    },
)

MDQ_WRITE_TOOLS: frozenset[str] = frozenset({"index_paths", "refresh_index"})

# Local git operation tools (git-mcp, port 8014)
GIT_READ_TOOLS: frozenset[str] = frozenset(
    {
        "git_status",
        "git_log",
        "git_diff",
        "git_branch",
        "git_show",
    }
)

GIT_WRITE_TOOLS: frozenset[str] = frozenset(
    {
        "git_add",
        "git_commit",
        "git_checkout",
        "git_pull",
        "git_push",
    }
)

GIT_TOOLS: frozenset[str] = GIT_READ_TOOLS | GIT_WRITE_TOOLS

# Shell execution tools (shell-mcp)
SHELL_TOOLS: frozenset[str] = frozenset({"shell_run"})

# Web search tools (web-search-mcp) — includes browser_fetch, the read-only
# page fetch + render-to-text tool merged into web-search-mcp from the
# retired standalone browser-mcp server.
WEB_SEARCH_TOOLS: frozenset[str] = frozenset({"search_web", "browser_fetch"})

# Tools a server withholds from /v1/tools (and so from config tool_names) while a config
# prerequisite is unmet, e.g. web-search-mcp's browser_fetch with an empty
# browser_allowed_domains. They stay registered as the static ownership seed, and drift
# validation does not report their absence from config or from the live response.
CONFIG_GATED_TOOLS: frozenset[str] = frozenset({"browser_fetch"})

# GitHub tools (github-mcp, port 8006)
GITHUB_READ_TOOLS: frozenset[str] = frozenset(
    {
        "github_search_repositories",
        "github_list_branches",
        "github_list_commits",
        "github_get_commit",
        "github_search_code",
        "github_get_file_contents",
        "github_list_issues",
        "github_get_issue",
        "github_search_issues",
        "github_list_pull_requests",
        "github_get_pull_request",
        "github_search_pull_requests",
    }
)

GITHUB_WRITE_TOOLS: frozenset[str] = frozenset(
    {
        "github_create_branch",
        "github_create_or_update_file",
        "github_push_files",
        "github_create_issue",
        "github_add_issue_comment",
        "github_create_pull_request",
        "github_update_pull_request",
    }
)

GITHUB_DANGEROUS_TOOLS: frozenset[str] = frozenset(
    {
        "github_delete_file",
        "github_merge_pull_request",
    }
)

GITHUB_TOOLS: frozenset[str] = (
    GITHUB_READ_TOOLS | GITHUB_WRITE_TOOLS | GITHUB_DANGEROUS_TOOLS
)

# Retry-classification reference data (ADR-004, dispatch retry policy; ADR-008
# owns the disposable dedup-store semantics this classification feeds). The
# authority for retry classification is each tool's declared `retry_policy`
# field (shared.tool_metadata.RetryPolicy); this frozenset remains as reference
# data, drift-checked against the declarations in tests/shared/test_tool_constants.py
# (mcpdl003 REQ-005 retired the shared config `[retry_class]` mirror).
# A tool in this set is 'retryable' (dispatch-capable: a failed call can be
# safely re-dispatched and deduplicated); every other tool — including unknown
# ones — is 'non_retryable' (fail-safe).
RETRYABLE_TOOLS: frozenset[str] = frozenset(
    {
        # file_write server (file_write)
        "write_file",
        "edit_file",
        "create_directory",
        "move_file",
        # file_delete server (file_delete)
        "delete_file",
        "delete_directory",
        # git server (git)
        "git_add",
        "git_commit",
        "git_checkout",
        "git_pull",
        "git_push",
        # github server (github)
        "github_add_issue_comment",
        "github_create_branch",
        "github_create_issue",
        "github_create_or_update_file",
        "github_delete_file",
        "github_merge_pull_request",
        "github_push_files",
        "github_update_pull_request",
        # mdq server (mdq)
        "index_paths",
        "refresh_index",
        # rag_pipeline server (rag_pipeline)
        "rag_delete_document",
    }
)

# Side-effect-classification reference data (ADR-004, sideeffect001): reference
# membership for the drift checks around the dispatch dedup gate, the HTTP
# fail-closed write gate, and the server.py REQ-004 idempotency-key boundary.
# The authority for side-effect membership is each tool's declared
# `side_effect_class` field (shared.tool_metadata.SideEffectClass); this set only
# detects drift against those declarations. Independent of the retry-class
# dimension (RETRYABLE_TOOLS above) and of the safety tier — the declared fields
# are separate dimensions and must not be conflated. This set reports drift, it
# does not decide or route anything.
ALL_SIDE_EFFECTING_TOOLS: frozenset[str] = (
    WRITE_TOOLS
    | DELETE_TOOLS
    | GIT_WRITE_TOOLS
    | RAG_WRITE_TOOLS
    | MDQ_WRITE_TOOLS
    | CICD_WRITE_TOOLS
    | GITHUB_WRITE_TOOLS
    | GITHUB_DANGEROUS_TOOLS
    | SHELL_TOOLS
)


def get_all_mcp_tool_names() -> frozenset[str]:
    """Return all known MCP tool names for conflict checking.

    Reference data for name-coverage and naming-conflict drift checks. The live
    `/v1/tools` declarations (RuntimeToolRegistry) are the authority for which
    tools exist; a mismatch with this set is reported as drift, not resolved by
    this set.
    """
    return (
        READ_TOOLS
        | WRITE_TOOLS
        | DELETE_TOOLS
        | RAG_TOOLS
        | CICD_TOOLS
        | MDQ_TOOLS
        | GIT_TOOLS
        | SHELL_TOOLS
        | WEB_SEARCH_TOOLS
        | GITHUB_TOOLS
    )
