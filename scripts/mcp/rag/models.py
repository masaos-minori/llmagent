#!/usr/bin/env python3
"""mcp/rag/models.py
Pydantic models for RAG pipeline request/response handling.
"""

from __future__ import annotations

from pydantic import BaseModel


class RAGPipelineRequest(BaseModel):
    query: str
    context: str | None = None
    max_results: int | None = 10


class RAGPipelineDebugRequest(BaseModel):
    query: str
    context: str | None = None
    max_results: int | None = 10


class RAGPipelineResponse(BaseModel):
    results: list[str]


class RAGPipelineDebugResponse(BaseModel):
    results: list[str]
    debug_info: dict[str, str]
