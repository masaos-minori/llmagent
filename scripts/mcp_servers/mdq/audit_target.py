#!/usr/bin/env python3
"""scripts/mcp_servers/mdq/audit_target.py

Audit target extraction for mdq-mcp server tools (REQ-006 redaction).

Values that must stay comparable across calls are hashed; a path inside an authorized
root becomes a root-relative identifier and a path outside one becomes a hash. No raw
query, regex, chunk identifier, or absolute path reaches a persisted record, so the
target is safe to store while still identifying which call it describes.

The roots are supplied by the caller rather than read here: they are the same roots the
authorization decision used, and reading configuration would add I/O to this module.

Dependency direction: audit_target → models
Import from here:  from mcp_servers.mdq.audit_target import extract_audit_target
"""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from mcp_servers.audit import hash_query_value, path_identifier


def extract_audit_target(
    tool_name: str, args: dict[str, Any], roots: Sequence[str] = ()
) -> str:
    """Extract the redacted audit target for one tool call.

    `roots` are the authorized roots in effect for this call. When none are supplied the
    path branches fall back to the hash form, which is the fail-closed behavior: no
    identifier is emitted for a call that has no authorized root.
    """
    match tool_name:
        case "search_docs":
            query = str(args.get("query", ""))
            path_prefix = str(args.get("path_prefix", ""))
            if not query:
                return ""
            hashed = hash_query_value(query)
            if not path_prefix:
                return hashed
            # The prefix is a path, so it goes through the same rule as a path argument; a
            # relative prefix inside no root hashes, which keeps the record free of
            # configured root names.
            return f"{hashed} + {path_identifier(path_prefix, roots)}"
        case "get_chunk":
            # An opaque identifier is hashed rather than shortened: a truncated prefix of
            # it would still leak the beginning of a value the caller treats as a secret.
            # An absent argument has no value to redact, so it stays empty.
            chunk_id = args.get("chunk_id", "")
            return hash_query_value(str(chunk_id)) if chunk_id else ""
        case "outline":
            path = args.get("path", "")
            return path_identifier(str(path), roots) if path else ""
        case "index_paths" | "refresh_index":
            paths = args.get("paths", [])
            return path_identifier(str(paths[0]), roots) if paths else ""
        case "grep_docs":
            pattern = args.get("pattern", "")
            return hash_query_value(str(pattern)) if pattern else ""
        case "stats":
            return "mdq-mcp"
        case _:
            return ""
