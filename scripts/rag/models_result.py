#!/usr/bin/env python3
"""rag/models_result.py

Result DTOs for the RAG and ingestion layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

from rag.enums import MqeStatus


class ResultSource(StrEnum):
    REMOTE = "remote"
    LOCAL = "local"
    FALLBACK = "fallback"


class HttpResultKind(StrEnum):
    SUCCESS = "success"
    EMPTY = "empty"
    ERROR = "error"
    NOT_USED = "not_used"


@dataclass(frozen=True)
class ExpandedQuerySet:
    status: MqeStatus
    queries: list[str]


@dataclass(frozen=True)
class SkipInfo:
    path: str
    reason: str


@dataclass(frozen=True)
class RagSearchRequest:
    query: str
    top_k: int = 5


@dataclass(frozen=True)
class RagSearchResult:
    query: str
    hits: list[Any]  # list[RankedHit] — typed after Phase 3-1
    context_str: str


@dataclass(frozen=True)
class PipelineExecutionResult:
    success: bool
    processed: int
    failed: int
    errors: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SearchDocsResult:
    query: str
    results: list[str]
    total: int


@dataclass(frozen=True)
class SanitizeResult:
    text: str
    was_sanitized: bool
    patterns_detected: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class SearchDiagnostics:
    embed_ok: int = 0
    embed_failed: int = 0
    fts_errors: int = 0
    # Remote mode fields (new):
    result_source: ResultSource = ResultSource.LOCAL
    http_result_kind: HttpResultKind = HttpResultKind.NOT_USED
    remote_status_code: int | None = None
    remote_latency_ms: float | None = None
    fallback_reason: str | None = None
