#!/usr/bin/env python3
"""mcp/sqlite/tools.py
MCP tool schema definitions for sqlite-mcp server (inputSchema format).
"""

from __future__ import annotations

from typing import Any

_MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "query_sqlite",
        "description": (
            "Execute a read-only SELECT query against a named SQLite database. "
            "Only SELECT statements are permitted. "
            "Results are capped at max_rows (default: 100)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "db": {
                    "type": "string",
                    "description": "Database name (e.g., 'rag' or 'session')",
                },
                "sql": {
                    "type": "string",
                    "description": "SELECT query string (non-SELECT statements are rejected)",
                },
            },
            "required": ["db", "sql"],
        },
    },
]
