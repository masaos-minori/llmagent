#!/usr/bin/env python3
"""mcp_servers/web_search/tools.py
MCP tool schema definitions for web-search-mcp server (inputSchema format).
"""

from __future__ import annotations

from typing import Any

TOOL_LIST: list[dict[str, Any]] = [
    {
        "name": "search_web",
        "description": (
            "Search the web for the latest information. "
            "Use when the local DB does not contain the needed information"
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query string"},
                "max_results": {
                    "type": "integer",
                    "description": "Maximum number of results (default: configured)",
                },
            },
            "required": ["query"],
        },
        "status": "production",
    },
]
