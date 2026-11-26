#!/usr/bin/env python3
"""scripts/mcp_servers/web_search/web_search_tools.py

MCP tool schema definitions for web-search-mcp server (inputSchema format).
"""

from __future__ import annotations

from shared.tool_metadata import TOOL_FIELD_SET_VERSION

from mcp_servers.models import McpTool
from mcp_servers.request_contract import build_input_schema
from mcp_servers.web_search.web_search_models import (
    BrowserFetchRequest,
    SearchRequest,
)

TOOL_LIST: list[McpTool] = [
    {
        "name": "search_web",
        "description": (
            "Search the web for the latest information. Use when the local DB does not contain the needed information"
        ),
        "inputSchema": build_input_schema(SearchRequest),
        "status": "production",
        "config_dependent": False,
        "is_write": False,
        "agent_safety_tier": "READ_ONLY",
        "side_effect_class": "read_only",
        "retry_policy": "safe_read_retry",
        "reconciliation_policy": "not_required",
        "idempotency_required": False,
        "preview_capability": "none",
        "policy_version": TOOL_FIELD_SET_VERSION,
        "requires_serial": False,
        "resource_scope_kind": "",
        "resource_scope_keys": {},
    },
    {
        "name": "browser_fetch",
        "description": (
            "Fetch a URL and return its visible text content (read-only; no JavaScript "
            "execution, no interactive actions). Host must be in the configured domain "
            "allowlist."
        ),
        "inputSchema": build_input_schema(BrowserFetchRequest),
        "status": "production",
        "config_dependent": True,
        "is_write": False,
        "agent_safety_tier": "READ_ONLY",
        "side_effect_class": "read_only",
        "retry_policy": "safe_read_retry",
        "reconciliation_policy": "not_required",
        "idempotency_required": False,
        "preview_capability": "none",
        "policy_version": TOOL_FIELD_SET_VERSION,
        "requires_serial": False,
        "resource_scope_kind": "",
        "resource_scope_keys": {},
    },
]
