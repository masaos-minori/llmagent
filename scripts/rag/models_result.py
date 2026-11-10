#!/usr/bin/env python3
"""scripts/rag/models_result.py

Result DTOs for the RAG and ingestion layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from rag.diagnostics import (
        PipelineDiagnostics,  # noqa: F401 — re-exported for consumers
    )

from rag.enums import MqeStatus


@dataclass(frozen=True)
class ExpandedQuerySet:
    """Expanded query set returned by MQE processing."""

    status: MqeStatus
    queries: list[str]


@dataclass(frozen=True)
class SkipInfo:
    """Information about a skipped document during ingestion."""

    path: str
    reason: str


@dataclass(frozen=True)
class RagSearchRequest:
    """Request parameters for a RAG search operation."""

    query: str
    top_k: int = 5


@dataclass(frozen=True)
class RagSearchResult:
    """Result of a RAG search operation."""

    query: str
    hits: list[Any]  # list[RankedHit] — typed after Phase 3-1
    context_str: str


@dataclass(frozen=True)
class PipelineExecutionResult:
    """Result of executing a RAG pipeline."""

    success: bool
    processed: int
    failed: int
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SearchDocsResult:
    """Result of searching documents via the MDQ store."""

    query: str
    results: list[str]
    total: int


@dataclass(frozen=True)
class SanitizeResult:
    """Result of sanitizing text content."""

    text: str
    was_sanitized: bool
    patterns_detected: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SearchDiagnostics:
    """Diagnostic information about a search operation."""

    embed_ok: int = 0
    embed_failed: int = 0
    fts_errors: int = 0
    degraded: bool = False
    fallback_reason: str | None = None
    # Corpus identity field (RAGCORPUS001 REQ-004): the selected corpus ``index_generation``.
    corpus_generation: int | None = None
