#!/usr/bin/env python3
"""mcp/rag_pipeline/tools.py
MCP tool schema definitions for rag-pipeline-mcp server (inputSchema format).
"""

from __future__ import annotations

from typing import Any

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
    },
]
