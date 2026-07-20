#!/usr/bin/env python3
"""mcp_servers/browser/tools.py

MCP tool schema definitions for browser-mcp server (inputSchema format).
"""

from __future__ import annotations

from typing import Any

TOOL_LIST: list[dict[str, Any]] = [
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
