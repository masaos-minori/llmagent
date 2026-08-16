#!/usr/bin/env python3
"""scripts/mcp_servers/mdq/audit_target.py

Audit target extraction for mdq-mcp server tools.

Dependency direction: audit_target → models
Import from here:  from mcp_servers.mdq.audit_target import extract_audit_target
"""

from __future__ import annotations

from typing import Any


def extract_audit_target(tool_name: str, args: dict[str, Any]) -> str:
    """Extract audit target based on tool name."""
    match tool_name:
        case "search_docs":
            query = str(args.get("query", ""))
            path = str(args.get("path_prefix", ""))
            return f"{query}{' + ' + path if path else ''}"
        case "get_chunk":
            return str(args.get("chunk_id", ""))[:80]
        case "outline":
            return str(args.get("path", ""))[:80]
        case "index_paths" | "refresh_index":
            paths = args.get("paths", [])
            return str(paths[0])[:80] if paths else ""
        case "grep_docs":
            return str(args.get("pattern", ""))[:80]
        case "stats":
            return "mdq-mcp"
        case _:
            return ""
