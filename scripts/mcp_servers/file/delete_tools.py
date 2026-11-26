#!/usr/bin/env python3
"""scripts/mcp_servers/file/delete_tools.py

MCP tool schema definitions for file-delete-mcp server (inputSchema format).

Schemas are generated from the Pydantic request models in delete_models.py via the
shared `build_input_schema()` generator so that tool definitions and models stay
in sync.

Dependency direction: mcp_servers.file.delete_tools → mcp_servers.request_contract
"""

from __future__ import annotations

from shared.tool_metadata import TOOL_FIELD_SET_VERSION

from mcp_servers.file.delete_models import (
    DeleteDirectoryRequest,
    DeleteFileRequest,
)
from mcp_servers.models import McpTool
from mcp_servers.request_contract import build_input_schema

# Shared metadata block: every tool in this module is a filesystem write keyed on a
# single "path" argument, so these fields are byte-for-byte identical across all
# TOOL_LIST entries. Kept inline for clarity.
TOOL_LIST: list[McpTool] = [
    {
        "name": "delete_file",
        "description": "Delete the specified file. When dry_run=true, return file info without deleting",
        "inputSchema": build_input_schema(DeleteFileRequest),
        "status": "production",
        "config_dependent": False,
        "is_write": True,
        "agent_safety_tier": "WRITE_DANGEROUS",
        "side_effect_class": "local_write",
        "retry_policy": "same_logical_call_only",
        "reconciliation_policy": "local_state",
        "idempotency_required": True,
        "preview_capability": "dry_run",
        "policy_version": TOOL_FIELD_SET_VERSION,
        "requires_serial": False,
        "resource_scope_kind": "filesystem",
        "resource_scope_keys": {"path": "path"},
    },
    {
        "name": "delete_directory",
        "description": "Delete a directory. When recursive=true, delete contents recursively. When dry_run=true, return directory info without deleting",
        "inputSchema": build_input_schema(DeleteDirectoryRequest),
        "status": "production",
        "config_dependent": False,
        "is_write": True,
        "agent_safety_tier": "WRITE_DANGEROUS",
        "side_effect_class": "local_write",
        "retry_policy": "same_logical_call_only",
        "reconciliation_policy": "local_state",
        "idempotency_required": True,
        "preview_capability": "dry_run",
        "policy_version": TOOL_FIELD_SET_VERSION,
        "requires_serial": False,
        "resource_scope_kind": "filesystem",
        "resource_scope_keys": {"path": "path"},
    },
]
