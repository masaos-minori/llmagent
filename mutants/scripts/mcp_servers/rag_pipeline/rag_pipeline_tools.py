#!/usr/bin/env python3
"""scripts/mcp_servers/rag_pipeline/rag_pipeline_tools.py

MCP tool schema definitions for rag-pipeline-mcp server (inputSchema format).
"""

from __future__ import annotations

from typing import Any

# Shared metadata: "is_write"/"requires_serial"/"resource_scope_kind" are
# byte-for-byte identical across the 3 read-only TOOL_LIST entries
# (rag_run_pipeline, rag_debug_pipeline, rag_list_documents). "status" stays
# per-entry (before this block) and "resource_scope_keys" stays per-entry
# (after this block) even though also identical among these entries (always
# []), since it is a mutable list value and per-entry literals avoid any risk
# of TOOL_LIST entries unintentionally sharing one list object (mirrors the
# analogous _MDQ_READONLY_METADATA/_MDQ_WRITE_METADATA split in
# scripts/mcp_servers/mdq/mdq_tools.py).
_RAG_PIPELINE_READONLY_METADATA: dict[str, Any] = {
    "is_write": False,
    "requires_serial": False,
    "resource_scope_kind": "",
}

# Shared metadata for the 1 write/serialized TOOL_LIST entry
# (rag_delete_document). See _RAG_PIPELINE_READONLY_METADATA above for why
# "resource_scope_keys" stays per-entry.
_RAG_PIPELINE_WRITE_METADATA: dict[str, Any] = {
    "is_write": True,
    "requires_serial": True,
    "resource_scope_kind": "rag_store",
}

TOOL_LIST: list[dict[str, Any]] = [
    {
        "name": "rag_run_pipeline",
        "description": "Run the full RAG pipeline (MQE→Search→RRF→Rerank→Dedup→Augment) for multi-format, semantic retrieval. Production-ready.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Original user query."},
                "history_context": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Recent user utterances used only for MQE.",
                },
                "debug": {
                    "type": "boolean",
                    "description": "Return intermediate outputs when true.",
                },
            },
            "required": ["query"],
        },
        "status": "production",
        **_RAG_PIPELINE_READONLY_METADATA,
        "resource_scope_keys": [],
    },
    {
        "name": "rag_debug_pipeline",
        "description": "Run the RAG pipeline and return all intermediate stage outputs for debugging. Multi-format, semantic retrieval. Production-ready.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Original user query."},
                "history_context": {
                    "type": "array",
                    "items": {"type": "string"},
                },
            },
            "required": ["query"],
        },
        "status": "production",
        **_RAG_PIPELINE_READONLY_METADATA,
        "resource_scope_keys": [],
    },
    {
        "name": "rag_list_documents",
        "description": "List indexed documents in the production RAG store (multi-format: PDF, HTML, text, code, Markdown).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "lang": {
                    "type": "string",
                    "description": "Filter by language ('ja' or 'en').",
                },
                "limit": {
                    "type": "integer",
                    "description": "Max results (default 20).",
                },
            },
            "required": [],
        },
        "status": "production",
        **_RAG_PIPELINE_READONLY_METADATA,
        "resource_scope_keys": [],
    },
    {
        "name": "rag_delete_document",
        "description": "Delete a document and all its chunks from the production RAG store by URL (multi-format store).",
        "inputSchema": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "Exact document URL to delete.",
                },
            },
            "required": ["url"],
        },
        "status": "production",
        **_RAG_PIPELINE_WRITE_METADATA,
        "resource_scope_keys": [],
    },
]
