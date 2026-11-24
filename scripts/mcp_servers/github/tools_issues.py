#!/usr/bin/env python3
"""scripts/mcp_servers/github/tools_issues.py

MCP tool schema definitions for GitHub issues operations.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypedDict

from shared.tool_metadata import TOOL_FIELD_SET_VERSION, ResourceKeyKind

from mcp_servers.github.github_models_issues import (
    AddIssueCommentRequest,
    CreateIssueRequest,
    GetIssueRequest,
    ListIssuesRequest,
    SearchIssuesRequest,
)
from mcp_servers.models import McpTool
from mcp_servers.request_contract import build_input_schema


# Shared metadata fields: "status" and "config_dependent" are byte-for-byte
# identical across all 5 TOOL_LIST entries, so they are split into a head
# (before "is_write"). "is_write" varies per entry and stays inline. After
# "is_write", 4 of the 5 entries also share an identical "requires_serial" +
# "resource_scope_kind" + "resource_scope_keys" tail (github_repo scope);
# github_search_issues is unscoped, so it gets its own tail with the same
# "requires_serial" value but an empty scope. Extracted so the shared parts
# stay in sync (mirrors the analogous _GITHUB_FILE_TOOL_METADATA_HEAD/_TAIL
# split in scripts/mcp_servers/github/tools_file.py).
class _GithubIssueMetadataHead(TypedDict):
    """Shared metadata fields common to github_issue TOOL_LIST entries."""

    policy_version: str
    status: str
    config_dependent: bool


class _GithubIssueRepoScopeTail(TypedDict):
    """Shared metadata tail for github_repo-scoped TOOL_LIST entries."""

    requires_serial: bool
    resource_scope_kind: str
    resource_scope_keys: Mapping[str, ResourceKeyKind]


class _GithubIssueNoScopeTail(TypedDict):
    """Shared metadata tail for unscoped TOOL_LIST entries."""

    requires_serial: bool
    resource_scope_kind: str
    resource_scope_keys: Mapping[str, ResourceKeyKind]


_GITHUB_ISSUE_TOOL_METADATA_HEAD: _GithubIssueMetadataHead = {
    "status": "production",
    "config_dependent": True,
    "policy_version": TOOL_FIELD_SET_VERSION,
}
_GITHUB_ISSUE_REPO_SCOPE_TAIL: _GithubIssueRepoScopeTail = {
    "requires_serial": False,
    "resource_scope_kind": "github_repo",
    "resource_scope_keys": {"owner": "non_escalating", "repo": "repo"},
}
_GITHUB_ISSUE_NO_SCOPE_TAIL: _GithubIssueNoScopeTail = {
    "requires_serial": False,
    "resource_scope_kind": "",
    "resource_scope_keys": {},
}

TOOL_LIST: list[McpTool] = [
    {
        "name": "github_list_issues",
        "description": (
            "Retrieve the list of issues for a GitHub repository. "
            "Use to check bug reports, feature requests, and known issues"
        ),
        "inputSchema": build_input_schema(ListIssuesRequest),
        **_GITHUB_ISSUE_TOOL_METADATA_HEAD,
        "is_write": False,
        "agent_safety_tier": "READ_ONLY",
        "side_effect_class": "read_only",
        "retry_policy": "safe_read_retry",
        "reconciliation_policy": "not_required",
        "idempotency_required": False,
        "preview_capability": "none",
        **_GITHUB_ISSUE_REPO_SCOPE_TAIL,
    },
    {
        "name": "github_get_issue",
        "description": (
            "Retrieve a specific issue from a GitHub repository. Use to check issue details, body, and state"
        ),
        "inputSchema": build_input_schema(GetIssueRequest),
        **_GITHUB_ISSUE_TOOL_METADATA_HEAD,
        "is_write": False,
        "agent_safety_tier": "READ_ONLY",
        "side_effect_class": "read_only",
        "retry_policy": "safe_read_retry",
        "reconciliation_policy": "not_required",
        "idempotency_required": False,
        "preview_capability": "none",
        **_GITHUB_ISSUE_REPO_SCOPE_TAIL,
    },
    {
        "name": "github_create_issue",
        "description": (
            "Create an issue in a GitHub repository. Use to report bugs or request features"
        ),
        "inputSchema": build_input_schema(CreateIssueRequest),
        **_GITHUB_ISSUE_TOOL_METADATA_HEAD,
        "is_write": True,
        "agent_safety_tier": "WRITE_SAFE",
        "side_effect_class": "external_write",
        "retry_policy": "same_logical_call_only",
        "reconciliation_policy": "external_state",
        "idempotency_required": True,
        "preview_capability": "dry_run",
        **_GITHUB_ISSUE_REPO_SCOPE_TAIL,
    },
    {
        "name": "github_search_issues",
        "description": (
            "Keyword search for issues/PRs across all of GitHub. "
            "Use to cross-search known bugs and discussions for specific projects"
        ),
        "inputSchema": build_input_schema(SearchIssuesRequest),
        **_GITHUB_ISSUE_TOOL_METADATA_HEAD,
        "is_write": False,
        "agent_safety_tier": "READ_ONLY",
        "side_effect_class": "read_only",
        "retry_policy": "safe_read_retry",
        "reconciliation_policy": "not_required",
        "idempotency_required": False,
        "preview_capability": "none",
        **_GITHUB_ISSUE_NO_SCOPE_TAIL,
    },
    {
        "name": "github_add_issue_comment",
        "description": (
            "Post a comment to an issue in a GitHub repository. "
            "Use to report progress, ask questions, or add information"
        ),
        "inputSchema": build_input_schema(AddIssueCommentRequest),
        **_GITHUB_ISSUE_TOOL_METADATA_HEAD,
        "is_write": True,
        "agent_safety_tier": "WRITE_SAFE",
        "side_effect_class": "external_write",
        "retry_policy": "same_logical_call_only",
        "reconciliation_policy": "external_state",
        "idempotency_required": True,
        "preview_capability": "dry_run",
        **_GITHUB_ISSUE_REPO_SCOPE_TAIL,
    },
]
