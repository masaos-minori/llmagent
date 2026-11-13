#!/usr/bin/env python3
"""scripts/rag/models_result.py

Result DTOs for the RAG and ingestion layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from rag.enums import MqeStatus

if TYPE_CHECKING:
    from shared.types import RankedHit


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
    hits: list[RankedHit]
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

    @property
    def degraded(self) -> bool:
        """True when any embedding or FTS error occurred during the run."""
        return self.embed_failed > 0 or self.fts_errors > 0

    def to_dict(self) -> dict[str, object]:
        return {
            "embed_ok": self.embed_ok,
            "embed_failed": self.embed_failed,
            "fts_errors": self.fts_errors,
            "degraded": self.degraded,
        }
