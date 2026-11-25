#!/usr/bin/env python3
"""scripts/mcp_servers/github/tools_pull_requests.py

MCP tool schema definitions for GitHub pull request operations.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import TypedDict

from shared.tool_metadata import TOOL_FIELD_SET_VERSION, ResourceKeyKind

from mcp_servers.github.github_models_pull_requests import (
    CreatePullRequestRequest,
    GetPullRequestRequest,
    ListPullRequestsRequest,
    MergePullRequestRequest,
    SearchPullRequestsRequest,
    UpdatePullRequestRequest,
)
from mcp_servers.models import McpTool
from mcp_servers.request_contract import build_input_schema


# Shared metadata fields: "status" and "config_dependent" are byte-for-byte
# identical across all 6 TOOL_LIST entries, so they are split into a head
# (before "is_write"). "is_write" varies per entry and stays inline. After
# "is_write", 5 of the 6 entries also share an identical "requires_serial" +
# "resource_scope_kind" + "resource_scope_keys" tail (github_repo scope);
# github_search_pull_requests is unscoped, so it gets its own tail with the
# same "requires_serial" value but an empty scope. Extracted so the shared
# parts stay in sync (mirrors the analogous
# _GITHUB_ISSUE_TOOL_METADATA_HEAD/_GITHUB_ISSUE_REPO_SCOPE_TAIL/
# _GITHUB_ISSUE_NO_SCOPE_TAIL split in
# scripts/mcp_servers/github/tools_issues.py).
class _GithubPrMetadataHead(TypedDict):
    """Shared metadata fields common to github_pr TOOL_LIST entries."""

    policy_version: str
    status: str
    config_dependent: bool


class _GithubPrRepoScopeTail(TypedDict):
    """Shared metadata tail for github_repo-scoped TOOL_LIST entries."""

    requires_serial: bool
    resource_scope_kind: str
    resource_scope_keys: Mapping[str, ResourceKeyKind]


class _GithubPrNoScopeTail(TypedDict):
    """Shared metadata tail for unscoped TOOL_LIST entries."""

    requires_serial: bool
    resource_scope_kind: str
    resource_scope_keys: Mapping[str, ResourceKeyKind]


_GITHUB_PR_TOOL_METADATA_HEAD: _GithubPrMetadataHead = {
    "status": "production",
    "config_dependent": True,
    "policy_version": TOOL_FIELD_SET_VERSION,
}
_GITHUB_PR_REPO_SCOPE_TAIL: _GithubPrRepoScopeTail = {
    "requires_serial": False,
    "resource_scope_kind": "github_repo",
    "resource_scope_keys": {"owner": "non_escalating", "repo": "repo"},
}
_GITHUB_PR_NO_SCOPE_TAIL: _GithubPrNoScopeTail = {
    "requires_serial": False,
    "resource_scope_kind": "",
    "resource_scope_keys": {},
}

TOOL_LIST: list[McpTool] = [
    {
        "name": "github_list_pull_requests",
        "description": (
            "Retrieve the list of pull requests for a GitHub repository. Use to check pending reviews or past PRs"
        ),
        "inputSchema": build_input_schema(ListPullRequestsRequest),
        **_GITHUB_PR_TOOL_METADATA_HEAD,
        "is_write": False,
        "agent_safety_tier": "READ_ONLY",
        "side_effect_class": "read_only",
        "retry_policy": "safe_read_retry",
        "reconciliation_policy": "not_required",
        "idempotency_required": False,
        "preview_capability": "none",
        **_GITHUB_PR_REPO_SCOPE_TAIL,
    },
    {
        "name": "github_get_pull_request",
        "description": (
            "Retrieve a specific pull request from a GitHub repository. Use to check PR details, branch info, and body"
        ),
        "inputSchema": build_input_schema(GetPullRequestRequest),
        **_GITHUB_PR_TOOL_METADATA_HEAD,
        "is_write": False,
        "agent_safety_tier": "READ_ONLY",
        "side_effect_class": "read_only",
        "retry_policy": "safe_read_retry",
        "reconciliation_policy": "not_required",
        "idempotency_required": False,
        "preview_capability": "none",
        **_GITHUB_PR_REPO_SCOPE_TAIL,
    },
    {
        "name": "github_create_pull_request",
        "description": (
            "Create a pull request in a GitHub repository. Use to request a review of branch changes"
        ),
        "inputSchema": build_input_schema(CreatePullRequestRequest),
        **_GITHUB_PR_TOOL_METADATA_HEAD,
        "is_write": True,
        "agent_safety_tier": "WRITE_DANGEROUS",
        "side_effect_class": "external_write",
        "retry_policy": "never",
        "reconciliation_policy": "external_state",
        "idempotency_required": True,
        "preview_capability": "dry_run",
        **_GITHUB_PR_REPO_SCOPE_TAIL,
    },
    {
        "name": "github_search_pull_requests",
        "description": (
            "Keyword search for pull requests across all of GitHub. "
            "Use to cross-search PRs related to a specific feature"
        ),
        "inputSchema": build_input_schema(SearchPullRequestsRequest),
        **_GITHUB_PR_TOOL_METADATA_HEAD,
        "is_write": False,
        "agent_safety_tier": "READ_ONLY",
        "side_effect_class": "read_only",
        "retry_policy": "safe_read_retry",
        "reconciliation_policy": "not_required",
        "idempotency_required": False,
        "preview_capability": "none",
        **_GITHUB_PR_NO_SCOPE_TAIL,
    },
    {
        "name": "github_update_pull_request",
        "description": (
            "Update the title, body, or state of a GitHub pull request. Use to reopen or close a PR"
        ),
        "inputSchema": build_input_schema(UpdatePullRequestRequest),
        **_GITHUB_PR_TOOL_METADATA_HEAD,
        "is_write": True,
        "agent_safety_tier": "WRITE_DANGEROUS",
        "side_effect_class": "external_write",
        "retry_policy": "never",
        "reconciliation_policy": "external_state",
        "idempotency_required": True,
        "preview_capability": "dry_run",
        **_GITHUB_PR_REPO_SCOPE_TAIL,
    },
    {
        "name": "github_merge_pull_request",
        "description": (
            "Merge a GitHub pull request. Use to merge a PR after review is complete"
        ),
        "inputSchema": build_input_schema(MergePullRequestRequest),
        **_GITHUB_PR_TOOL_METADATA_HEAD,
        "is_write": True,
        "agent_safety_tier": "WRITE_DANGEROUS",
        "side_effect_class": "external_write",
        "retry_policy": "never",
        "reconciliation_policy": "external_state",
        "idempotency_required": True,
        "preview_capability": "dry_run",
        **_GITHUB_PR_REPO_SCOPE_TAIL,
    },
]
