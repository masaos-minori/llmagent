#!/usr/bin/env python3
"""mcp/mdq/tools.py
MCP tool schema definitions for mdq-mcp server (inputSchema format).
"""

from __future__ import annotations

from typing import Any

_MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "search_docs",
        "description": "Search indexed Markdown sections by query.",
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
                    "description": "Search mode: bm25/grep/hybrid",
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
            },
            "required": ["query"],
        },
        "status": "production",
    },
    {
        "name": "get_chunk",
        "description": "Retrieve a Markdown chunk by its ID.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "chunk_id": {"type": "integer", "description": "Chunk ID"},
                "with_neighbors": {
                    "type": "boolean",
                    "description": "Include adjacent headings",
                },
            },
            "required": ["chunk_id"],
        },
        "status": "production",
    },
    {
        "name": "outline",
        "description": "Get the heading structure of a Markdown file.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "File path"}},
            "required": ["path"],
        },
        "status": "production",
    },
    {
        "name": "index_paths",
        "description": "Index a set of paths into the in-process SQLite DB.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "paths": {"type": "array", "description": "Paths to index"},
            },
            "required": ["paths"],
        },
        "status": "production",
    },
    {
        "name": "refresh_index",
        "description": "Incrementally refresh the index for a set of paths.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "paths": {"type": "array", "description": "Paths to refresh"},
            },
            "required": ["paths"],
        },
        "status": "production",
    },
    {
        "name": "stats",
        "description": "Return document/chunk count and index metadata.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "status": "production",
    },
    {
        "name": "grep_docs",
        "description": "Search Markdown chunks with a regex pattern.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern"},
                "paths": {"type": "array", "description": "Optional path filter"},
            },
            "required": ["pattern"],
        },
        "status": "production",
    },
]
