#!/usr/bin/env python3
"""scripts/mcp_servers/file/write_tools.py

MCP tool schema definitions for file-write-mcp server (inputSchema format).

Schemas are generated from the Pydantic request models in write_models.py via the
shared `build_input_schema()` generator so that tool definitions and models stay
in sync.

Dependency direction: mcp_servers.file.write_tools → mcp_servers.request_contract
"""

from __future__ import annotations

from shared.tool_metadata import TOOL_FIELD_SET_VERSION

from mcp_servers.file.write_models import (
    CreateDirectoryRequest,
    EditFileRequest,
    MoveFileRequest,
    WriteFileRequest,
)
from mcp_servers.models import McpTool
from mcp_servers.request_contract import build_input_schema

TOOL_LIST: list[McpTool] = [
    {
        "name": "write_file",
        "description": "Create or overwrite a file. When dry_run=true, return only the diff without writing",
        "inputSchema": build_input_schema(WriteFileRequest),
        "status": "production",
        "config_dependent": False,
        "is_write": True,
        "agent_safety_tier": "WRITE_SAFE",
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
        "name": "edit_file",
        "description": "Apply string replacements to a file. When dry_run=true, return only the diff without writing",
        "inputSchema": build_input_schema(EditFileRequest),
        "status": "production",
        "config_dependent": False,
        "is_write": True,
        "agent_safety_tier": "WRITE_SAFE",
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
        "name": "create_directory",
        "description": "Create a directory, including parent directories recursively. When dry_run=true, return directory info without creating",
        "inputSchema": build_input_schema(CreateDirectoryRequest),
        "status": "production",
        "config_dependent": False,
        "is_write": True,
        "agent_safety_tier": "WRITE_SAFE",
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
        "name": "move_file",
        "description": "Move or rename a file or directory. When dry_run=true, return feasibility info without moving",
        "inputSchema": build_input_schema(MoveFileRequest),
        "status": "production",
        "config_dependent": False,
        "is_write": True,
        "agent_safety_tier": "WRITE_SAFE",
        "side_effect_class": "local_write",
        "retry_policy": "same_logical_call_only",
        "reconciliation_policy": "local_state",
        "idempotency_required": True,
        "preview_capability": "dry_run",
        "policy_version": TOOL_FIELD_SET_VERSION,
        "requires_serial": False,
        "resource_scope_kind": "filesystem",
        "resource_scope_keys": {
            "source": "path",
            "destination": "path",
        },
    },
]
