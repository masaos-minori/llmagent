#!/usr/bin/env python3
"""scripts/mcp_servers/shell/shell_tools.py

MCP tool schema definitions for shell-mcp server (inputSchema format).
"""

from __future__ import annotations

from mcp_servers.models import McpTool

TOOL_LIST: list[McpTool] = [
    {
        "name": "shell_run",
        "description": (
            "Execute a sandboxed shell command. "
            "argv[0] must be in the configured allowlist. "
            "cwd must be under an allowed directory."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "command": {
                    "type": "string",
                    "description": "Command string (argv[0] must be in allowlist)",
                },
                "argv": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Explicit argv list; when provided, used instead of shlex.split(command) to prevent shell injection",
                },
                "timeout_sec": {
                    "type": "integer",
                    "description": "Timeout in seconds (default: 30, max: server-configured)",
                },
                "cwd": {
                    "type": "string",
                    "description": "Working directory (must be under allowed dirs)",
                },
                "env": {
                    "type": "object",
                    "description": "Additional environment variables to merge",
                },
                "max_output_kb": {
                    "type": "integer",
                    "description": "Output size limit in KB (default: 512)",
                },
                "dry_run": {
                    "type": "boolean",
                    "description": "Preview only; command is not executed",
                },
            },
            "required": ["command"],
        },
        "status": "production",
        "config_dependent": True,
        "is_write": True,
        "requires_serial": True,
        "resource_scope_kind": "process",
        "resource_scope_keys": [],
    },
]
