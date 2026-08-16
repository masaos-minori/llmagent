#!/usr/bin/env python3
"""scripts/mcp_servers/mdq/mdq_tools.py

MCP tool schema definitions for mdq-mcp server (inputSchema format).
"""

from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class MCPToolSchema(TypedDict):
    """MCP tool definition following the MCP JSON-RPC schema format."""

    name: str
    description: str
    inputSchema: dict[str, Any]
    status: str
    is_write: NotRequired[bool]
    requires_serial: NotRequired[bool]
    resource_scope_kind: NotRequired[str]
    resource_scope_keys: NotRequired[list[str]]


class _MdqToolMetadataTail(TypedDict):
    """Shared trailing metadata fields common to a group of TOOL_LIST entries."""

    is_write: bool
    requires_serial: bool
    resource_scope_kind: str


# Shared metadata: "is_write"/"requires_serial"/"resource_scope_kind" are
# byte-for-byte identical across the 5 read-only TOOL_LIST entries
# (search_docs, get_chunk, outline, stats, grep_docs). "resource_scope_keys"
# is kept per-entry (mirrors the analogous precedent in read_tools.py /
# cicd_tools.py) since, although also identical among these entries (always
# []), it is a mutable list value and per-entry literals avoid any risk of
# TOOL_LIST entries unintentionally sharing one list object.
_MDQ_READONLY_METADATA: _MdqToolMetadataTail = {
    "is_write": False,
    "requires_serial": False,
    "resource_scope_kind": "",
}

# Shared metadata for the 2 write/serialized TOOL_LIST entries (index_paths,
# refresh_index). See _MDQ_READONLY_METADATA above for why
# "resource_scope_keys" stays per-entry.
_MDQ_WRITE_METADATA: _MdqToolMetadataTail = {
    "is_write": True,
    "requires_serial": True,
    "resource_scope_kind": "mdq_store",
}


TOOL_LIST: list[MCPToolSchema] = [
    {
        "name": "search_docs",
        "description": "Search indexed Markdown documents using BM25/FTS5. Markdown-only, structure-aware retrieval.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Search query string"},
                "limit": {
                    "type": "integer",
                    "description": (
                        "Max results to fetch (default: 10). Bounded at the database layer by "
                        "the server's configured max_results_limit — the effective SQL limit is "
                        "min(limit, configured max_results_limit)."
                    ),
                    "minimum": 1,
                    "maximum": 100,
                },
                "mode": {
                    "type": "string",
                    "description": "Search mode: bm25 (only supported value)",
                    "enum": ["bm25"],
                },
                "path_prefix": {
                    "type": "string",
                    "description": "Filter by path prefix",
                },
                "tag_filter": {
                    "type": "array",
                    "description": "Filter by tags",
                    "items": {"type": "string"},
                },
                "heading_prefix": {
                    "type": "string",
                    "description": "Filter by heading prefix",
                },
                "max_results_limit": {
                    "type": "integer",
                    "description": (
                        "Secondary display cap applied after the SQL-layer limit; if smaller "
                        "than the effective limit derived from 'limit', further restricts how "
                        "many results are shown (default: use server config value)."
                    ),
                    "minimum": 1,
                    "maximum": 100,
                },
                "max_total_result_chars": {
                    "type": "integer",
                    "description": "Max total characters in response (default: use config value)",
                    "minimum": 1,
                    "maximum": 100000,
                },
            },
            "required": ["query"],
        },
        "status": "production",
        **_MDQ_READONLY_METADATA,
        "resource_scope_keys": [],
    },
    {
        "name": "get_chunk",
        "description": "Retrieve a Markdown chunk by ID, with optional adjacent heading context. Markdown-only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "chunk_id": {"type": "string", "description": "Chunk ID"},
                "with_neighbors": {
                    "type": "boolean",
                    "description": "Include adjacent headings",
                },
                "max_chars_per_chunk": {
                    "type": "integer",
                    "description": "Max characters in chunk content (default: use config value)",
                    "minimum": 1,
                    "maximum": 10000,
                },
            },
            "required": ["chunk_id"],
        },
        "status": "production",
        **_MDQ_READONLY_METADATA,
        "resource_scope_keys": [],
    },
    {
        "name": "outline",
        "description": "Get the heading hierarchy of a Markdown file. Structure-aware, Markdown-only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "File path"},
                "max_outline_items": {
                    "type": "integer",
                    "description": "Max outline items (default: use config value)",
                    "minimum": 1,
                    "maximum": 500,
                },
                "max_depth": {
                    "type": "integer",
                    "description": "Max heading depth to include (default: use config value)",
                    "minimum": 1,
                    "maximum": 6,
                },
            },
            "required": ["path"],
        },
        "status": "production",
        **_MDQ_READONLY_METADATA,
        "resource_scope_keys": [],
    },
    {
        "name": "index_paths",
        "description": "Index Markdown file paths into the MDQ store. Markdown-only ingestion.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "paths": {
                    "type": "array",
                    "description": "Paths to index",
                    "items": {"type": "string"},
                    "minItems": 1,
                },
            },
            "required": ["paths"],
        },
        "status": "production",
        **_MDQ_WRITE_METADATA,
        "resource_scope_keys": ["paths"],
    },
    {
        "name": "refresh_index",
        "description": "Incrementally refresh the index for changed Markdown files. Markdown-only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "paths": {
                    "type": "array",
                    "description": "Paths to refresh",
                    "items": {"type": "string"},
                    "minItems": 1,
                },
                "force": {
                    "type": "boolean",
                    "description": "Force full re-index regardless of changes (default: false)",
                },
            },
            "required": ["paths"],
        },
        "status": "production",
        **_MDQ_WRITE_METADATA,
        "resource_scope_keys": ["paths"],
    },
    {
        "name": "stats",
        "description": "Return document/chunk counts and FTS5 index metadata for the Markdown store.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "status": "production",
        **_MDQ_READONLY_METADATA,
        "resource_scope_keys": [],
    },
    {
        "name": "grep_docs",
        "description": "Search Markdown chunks with a regex pattern. Structure-aware, Markdown-only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern"},
                "paths": {
                    "type": "array",
                    "description": "Optional path filter",
                    "items": {"type": "string"},
                },
                "max_grep_matches": {
                    "type": "integer",
                    "description": "Max grep matches (default: 200)",
                    "minimum": 1,
                    "maximum": 200,
                },
                "max_chars_per_match": {
                    "type": "integer",
                    "description": "Max chars per match snippet (default: 500)",
                    "minimum": 1,
                    "maximum": 500,
                },
                "context_before": {
                    "type": "integer",
                    "description": "Context lines before match (default: 2)",
                    "minimum": 0,
                },
                "context_after": {
                    "type": "integer",
                    "description": "Context lines after match (default: 2)",
                    "minimum": 0,
                },
            },
            "required": ["pattern"],
        },
        "status": "production",
        **_MDQ_READONLY_METADATA,
        "resource_scope_keys": [],
    },
]

# Write/admin tools that require serialization and concurrency limits.
_WRITE_TOOLS = frozenset(("index_paths", "refresh_index"))
