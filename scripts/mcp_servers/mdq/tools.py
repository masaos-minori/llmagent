#!/usr/bin/env python3
"""mcp_servers/mdq/tools.py

MCP tool schema definitions for mdq-mcp server (inputSchema format).
"""

from __future__ import annotations

from typing import Any, NotRequired, TypedDict


class MCPToolSchema(TypedDict):
    name: str
    description: str
    inputSchema: dict[str, Any]
    status: str
    is_write: NotRequired[bool]
    requires_serial: NotRequired[bool]


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
                    "description": "Max results (default: 10)",
                },
                "mode": {
                    "type": "string",
                    "description": "Search mode: bm25/grep (hybrid is not yet supported)",
                },
                "path_prefix": {
                    "type": "string",
                    "description": "Filter by path prefix",
                },
                "tag_filter": {"type": "array", "description": "Filter by tags"},
                "heading_prefix": {
                    "type": "string",
                    "description": "Filter by heading prefix",
                },
                "max_results_limit": {
                    "type": "integer",
                    "description": "Override max results from config (default: use config value)",
                },
                "max_total_result_chars": {
                    "type": "integer",
                    "description": "Max total characters in response (default: use config value)",
                },
            },
            "required": ["query"],
        },
        "status": "production",
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
                },
            },
            "required": ["chunk_id"],
        },
        "status": "production",
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
                },
            },
            "required": ["path"],
        },
        "status": "production",
    },
    {
        "name": "index_paths",
        "description": "Index Markdown file paths into the MDQ store. Markdown-only ingestion.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "paths": {"type": "array", "description": "Paths to index"},
            },
            "required": ["paths"],
        },
        "status": "production",
        "is_write": True,
        "requires_serial": True,
    },
    {
        "name": "refresh_index",
        "description": "Incrementally refresh the index for changed Markdown files. Markdown-only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "paths": {"type": "array", "description": "Paths to refresh"},
                "force": {
                    "type": "boolean",
                    "description": "Force full re-index regardless of changes (default: false)",
                },
            },
            "required": ["paths"],
        },
        "status": "production",
        "is_write": True,
        "requires_serial": True,
    },
    {
        "name": "stats",
        "description": "Return document/chunk counts and FTS5 index metadata for the Markdown store.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "status": "production",
    },
    {
        "name": "grep_docs",
        "description": "Search Markdown chunks with a regex pattern. Structure-aware, Markdown-only.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern"},
                "paths": {"type": "array", "description": "Optional path filter"},
                "max_grep_matches": {
                    "type": "integer",
                    "description": "Max grep matches (default: 200)",
                },
                "max_chars_per_match": {
                    "type": "integer",
                    "description": "Max chars per match snippet (default: 500)",
                },
                "context_before": {
                    "type": "integer",
                    "description": "Context lines before match (default: 2)",
                },
                "context_after": {
                    "type": "integer",
                    "description": "Context lines after match (default: 2)",
                },
            },
            "required": ["pattern"],
        },
        "status": "production",
    },
    {
        "name": "fts_consistency_check",
        "description": "Check FTS5 index consistency between chunks and chunks_fts tables. Admin operation.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "status": "admin",
    },
    {
        "name": "fts_rebuild",
        "description": "Rebuild the FTS5 index. Admin operation — may take time on large datasets.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "status": "admin",
    },
]

# Write/admin tools that require serialization and concurrency limits.
_WRITE_TOOLS = frozenset(("index_paths", "refresh_index"))
