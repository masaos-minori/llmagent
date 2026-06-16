#!/usr/bin/env python3
"""mcp/rag_pipeline/tools.py
MCP tool schema definitions for rag-pipeline-mcp server (inputSchema format).
"""

from __future__ import annotations

from typing import Any

_MCP_TOOLS: list[dict[str, Any]] = [
    {
        "name": "rag_run_pipeline",
        "description": (
            "Run MQE, Search, RRF, Rerank, Dedup and Augment as a single integrated"
            " RAG pipeline."
        ),
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
        "description": (
            "Run integrated RAG pipeline and return all intermediate stage outputs"
            " for debugging."
        ),
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
]
