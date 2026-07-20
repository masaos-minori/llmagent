#!/usr/bin/env python3
"""mcp_servers/web_search/tools.py

MCP tool schema definitions for web-search-mcp server (inputSchema format).
"""

from __future__ import annotations

from typing import Any

from mcp_servers.web_search.web_search_models import get_max_results_limit

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
    },
]
