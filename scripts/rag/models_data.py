#!/usr/bin/env python3
"""rag/models_data.py

Data DTOs for the RAG and ingestion layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from rag.enums import LanguageCode


@dataclass(frozen=True)
class EmbeddingResponse:
    embedding: list[float]
    model: str | None = None


@dataclass(frozen=True)
class CrawlTarget:
    url: str
    lang: LanguageCode


@dataclass(frozen=True)
class ChunkDocument:
    url: str
    title: str
    lang: str
    content: str
    code_blocks: list[str] = field(default_factory=list)
    etag: str | None = None
    last_modified: str | None = None
    chunking_strategy: str = "text"
    normalized_content: str | None = None
    chunk_index: int = 0
    source_file: str = ""
    chunk_type: str = ""


@dataclass(frozen=True)
class ChunkRecord:
    chunk_id: str
    url: str
    title: str
    lang: str
    content: str
    embedding: list[float] = field(default_factory=list)


@dataclass(frozen=True)
class RegisteredDocument:
    url: str
    lang: str
    chunk_count: int


@dataclass(frozen=True)
class CacheEntry:
    embedding: list[float]
    context_str: str
    history_context: str = ""
    generation: int = 0


@dataclass(frozen=True)
class TwoStageFetchResult:
    """Typed result capturing reranked hits with applied filter/dedup parameters."""

    hits: list[Any]  # list[RagHit] in-process; list[dict] HTTP mode
    min_score_applied: float  # rag_min_score used (0.0 = no score filter)
    max_chunks_per_doc: int  # per-doc dedup limit applied
