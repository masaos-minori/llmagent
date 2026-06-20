#!/usr/bin/env python3
"""mcp/mdq/tools.py
MCP tool schema definitions for mdq-mcp server (inputSchema format).
"""

from __future__ import annotations

from typing import Any

_MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "search_docs",
        "description": "Search indexed Markdown documents using BM25/FTS5. Markdown-only, structure-aware retrieval. Experimental.",
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
        "status": "stub",
    },
    {
        "name": "get_chunk",
        "description": "Retrieve a Markdown chunk by ID, with optional adjacent heading context. Markdown-only. Experimental.",
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
        "status": "stub",
    },
    {
        "name": "outline",
        "description": "Get the heading hierarchy of a Markdown file. Structure-aware, Markdown-only. Experimental.",
        "inputSchema": {
            "type": "object",
            "properties": {"path": {"type": "string", "description": "File path"}},
            "required": ["path"],
        },
        "status": "stub",
    },
    {
        "name": "index_paths",
        "description": "Index Markdown file paths into the MDQ store. Markdown-only ingestion. Experimental.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "paths": {"type": "array", "description": "Paths to index"},
            },
            "required": ["paths"],
        },
        "status": "stub",
    },
    {
        "name": "refresh_index",
        "description": "Incrementally refresh the index for changed Markdown files. Markdown-only. Experimental.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "paths": {"type": "array", "description": "Paths to refresh"},
            },
            "required": ["paths"],
        },
        "status": "stub",
    },
    {
        "name": "stats",
        "description": "Return document/chunk counts and FTS5 index metadata for the Markdown store. Experimental.",
        "inputSchema": {"type": "object", "properties": {}, "required": []},
        "status": "stub",
    },
    {
        "name": "grep_docs",
        "description": "Search Markdown chunks with a regex pattern. Structure-aware, Markdown-only. Experimental.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "Regex pattern"},
                "paths": {"type": "array", "description": "Optional path filter"},
            },
            "required": ["pattern"],
        },
        "status": "stub",
    },
]
