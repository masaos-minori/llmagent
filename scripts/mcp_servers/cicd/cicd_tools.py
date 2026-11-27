#!/usr/bin/env python3
"""scripts/mcp_servers/cicd/cicd_tools.py

MCP tool schema definitions for cicd-mcp server (inputSchema format).

Each `inputSchema` is generated from its strict request model through
`build_input_schema()`, so the contract a client discovers at `/v1/tools` is the
contract the server enforces at call time. Field descriptions live on the model
fields (`cicd_models.py`), not here.

Dependency direction: tools → models, request_contract
"""

from __future__ import annotations

from typing import TypedDict

from shared.tool_metadata import TOOL_FIELD_SET_VERSION

from mcp_servers.cicd.cicd_models import (
    GetWorkflowLogsRequest,
    GetWorkflowRunsRequest,
    GetWorkflowStatusRequest,
    TriggerWorkflowRequest,
)
from mcp_servers.models import McpTool
from mcp_servers.request_contract import build_input_schema


# Shared metadata fields: "requires_serial" and "resource_scope_kind" are
# byte-for-byte identical across all 4 TOOL_LIST entries, and "policy_version"
# carries the single field-set version value (schema 2.1, agentcfg003).
# "is_write", the policy fields and "resource_scope_keys" are kept per-entry
# because they vary (is_write is True only for trigger_workflow;
# resource_scope_keys differs per tool), so unlike the
# read_tools.py/write_tools.py/delete_tools.py/web_search_tools.py metadata-tail
# precedent (where the whole tail is uniform), only this 3-field sub-block is
# extracted here, positioned between the per-entry "is_write" and
# "resource_scope_keys" to preserve original key order.
class _CicdToolMetadataTail(TypedDict):
    """Shared trailing metadata fields common to cicd TOOL_LIST entries."""

    requires_serial: bool
    resource_scope_kind: str
    policy_version: str


_CICD_TOOL_METADATA_TAIL: _CicdToolMetadataTail = {
    "requires_serial": False,
    "resource_scope_kind": "cicd_workflow",
    "policy_version": TOOL_FIELD_SET_VERSION,
}

TOOL_LIST: list[McpTool] = [
    {
        "name": "trigger_workflow",
        "description": (
            "Trigger a GitHub Actions workflow dispatch event. "
            "Requires the repo to be in repo_allowlist. "
            "When dry_run=true, preview only without triggering dispatch."
        ),
        "inputSchema": build_input_schema(TriggerWorkflowRequest),
        "status": "production",
        "config_dependent": True,
        "is_write": True,
        **_CICD_TOOL_METADATA_TAIL,
        "agent_safety_tier": "WRITE_DANGEROUS",
        "side_effect_class": "external_write",
        "retry_policy": "never",
        "reconciliation_policy": "external_state",
        "idempotency_required": True,
        "preview_capability": "none",
        "resource_scope_keys": {
            "repo": "repo",
            "workflow": "non_escalating",
            "ref": "branch",
        },
    },
    {
        "name": "get_workflow_runs",
        "description": (
            "List recent workflow runs for a repository. Returns run status, conclusion, timestamps, and URLs."
        ),
        "inputSchema": build_input_schema(GetWorkflowRunsRequest),
        "status": "production",
        "config_dependent": True,
        "is_write": False,
        **_CICD_TOOL_METADATA_TAIL,
        "agent_safety_tier": "READ_ONLY",
        "side_effect_class": "read_only",
        "retry_policy": "safe_read_retry",
        "reconciliation_policy": "not_required",
        "idempotency_required": False,
        "preview_capability": "none",
        "resource_scope_keys": {"repo": "repo", "workflow": "non_escalating"},
    },
    {
        "name": "get_workflow_status",
        "description": (
            "Get the current status and details of a specific workflow run by run ID."
        ),
        "inputSchema": build_input_schema(GetWorkflowStatusRequest),
        "status": "production",
        "config_dependent": True,
        "is_write": False,
        **_CICD_TOOL_METADATA_TAIL,
        "agent_safety_tier": "READ_ONLY",
        "side_effect_class": "read_only",
        "retry_policy": "safe_read_retry",
        "reconciliation_policy": "not_required",
        "idempotency_required": False,
        "preview_capability": "none",
        "resource_scope_keys": {"repo": "repo", "run_id": "non_escalating"},
    },
    {
        "name": "get_workflow_logs",
        "description": (
            "Retrieve job summaries and log text for a workflow run. "
            "Output is capped at max_log_size_kb (default: 256 KB)."
        ),
        "inputSchema": build_input_schema(GetWorkflowLogsRequest),
        "status": "production",
        "config_dependent": True,
        "is_write": False,
        **_CICD_TOOL_METADATA_TAIL,
        "agent_safety_tier": "READ_ONLY",
        "side_effect_class": "read_only",
        "retry_policy": "safe_read_retry",
        "reconciliation_policy": "not_required",
        "idempotency_required": False,
        "preview_capability": "none",
        "resource_scope_keys": {"repo": "repo", "run_id": "non_escalating"},
    },
]
