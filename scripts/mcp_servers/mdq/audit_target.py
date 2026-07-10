#!/usr/bin/env python3
"""mcp_servers/mdq/audit_target.py

Audit target extraction for mdq-mcp server tools.

Dependency direction: audit_target → models
Import from here:  from mcp_servers.mdq.audit_target import extract_audit_target
"""

from __future__ import annotations

from typing import Any


def extract_audit_target(tool_name: str, args: dict[str, Any]) -> str:
    """Extract audit target based on tool name."""
    if tool_name == "search_docs":
        query = str(args.get("query", ""))
        path = str(args.get("path_prefix", ""))
        return f"{query}{' + ' + path if path else ''}"
    if tool_name == "get_chunk":
        return str(args.get("chunk_id", ""))[:80]
    if tool_name == "outline":
        return str(args.get("path", ""))[:80]
    if tool_name in ("index_paths", "refresh_index"):
        paths = args.get("paths", [])
        return str(paths[0])[:80] if paths else ""
    if tool_name == "grep_docs":
        return str(args.get("pattern", ""))[:80]
    if tool_name in ("stats", "fts_consistency_check", "fts_rebuild"):
        return "mdq-mcp"
    return ""
