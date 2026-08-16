#!/usr/bin/env python3
"""scripts/mcp_servers/web_search/web_search_tools.py

MCP tool schema definitions for web-search-mcp server (inputSchema format).
"""

from __future__ import annotations

from typing import Any

from mcp_servers.web_search.web_search_models import get_max_results_limit

# Shared metadata tail: every tool in this module has identical is_write/
# requires_serial/resource_scope_kind/resource_scope_keys values (neither tool
# scopes to a resource). Extracted so they stay in sync (mirrors the analogous
# _FILESYSTEM_READ_METADATA extraction in scripts/mcp_servers/file/read_tools.py).
# "status" and "config_dependent" are kept per-entry: browser_fetch carries
# config_dependent (True) between "status" and this tail, so folding it into
# the shared block would change each entry's key insertion order relative to
# the original definitions.
_WEB_SEARCH_TOOL_METADATA_TAIL: dict[str, Any] = {
    "is_write": False,
    "requires_serial": False,
    "resource_scope_kind": "",
    "resource_scope_keys": [],
}

TOOL_LIST: list[dict[str, Any]] = [
    {
        "name": "search_web",
        "description": (
            "Search the web for the latest information. Use when the local DB does not contain the needed information"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query string",
                    "minLength": 1,
                    "maxLength": 500,
                },
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: configured)",
                    "minimum": 1,
                    "maximum": get_max_results_limit(),
                },
            },
            "required": ["query"],
        },
        "status": "production",
        **_WEB_SEARCH_TOOL_METADATA_TAIL,
    },
    {
        "name": "browser_fetch",
        "description": (
            "Fetch a URL and return its visible text content (read-only; no JavaScript "
            "execution, no interactive actions). Host must be in the configured domain "
            "allowlist."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Absolute http(s) URL to fetch (host must be allowlisted)",
                },
                "max_response_kb": {
                    "type": "integer",
                    "description": (
                        "Output size limit in KB (default: server-configured; caller "
                        "value is clamped to server maximum)"
                    ),
                },
            },
            "required": ["url"],
        },
        "status": "production",
        "config_dependent": True,
        **_WEB_SEARCH_TOOL_METADATA_TAIL,
    },
]
