#!/usr/bin/env python3
"""scripts/rag/models_data.py

Data DTOs for the RAG and ingestion layers.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class EmbeddingResponse:
    """Response from an embedding API call."""

    embedding: list[float]
    model: str | None = None


@dataclass(frozen=True)
class ChunkDocument:
    """Raw document ready for chunking during ingestion."""

    url: str
    title: str
    lang: str
    content: str
    chunking_strategy: str
    chunk_index: int
    source_file: str
    chunk_type: str
    fetched_at: str
    code_blocks: list[str] = field(default_factory=list)
    etag: str | None = None
    last_modified: str | None = None
    normalized_content: str | None = None


@dataclass(frozen=True)
class CrawlDocument:
    """Raw document ready for crawling during ingestion."""

    url: str
    title: str
    lang: str
    fetched_at: str
    content: str
    code_blocks: list[str] = field(default_factory=list)
    etag: str | None = None
    last_modified: str | None = None


@dataclass(frozen=True)
class ChunkRecord:
    """Indexed chunk record stored in SQLite."""

    chunk_id: str
    url: str
    title: str
    lang: str
    content: str
    embedding: list[float] = field(default_factory=list)


@dataclass(frozen=True)
class PreparedChunk:
    """Chunk with a generated embedding, ready for DB insertion during ingestion."""

    doc_id: int
    chunk_index: int
    content: str
    normalized_content: str | None
    embedding_blob: bytes
    chunk_type: str
    source_file: str


@dataclass(frozen=True)
class ChunkSettings:
    """Immutable chunking settings aggregated from ``chunk_splitter.toml``.

    Constructed once in ``ChunkSplitter.__init__`` and shared with the English and
    Japanese chunk mixins so they read one collaborator instead of reading the
    scattered undeclared host attributes they previously depended on (ragcrv006,
    REQ-001). Field order mirrors the inline assignments in ``__init__``.
    """

    min_chunk: int
    max_chunk: int
    chunk_overlap: int
    md_snippet_max_chars: int
    md_index_enable: bool
    en_stopwords: frozenset[str]
    ja_stop_pos: frozenset[str]


@dataclass(frozen=True)
class TwoStageFetchResult:
    """Typed result capturing reranked hits with applied filter/dedup parameters."""

    hits: list[Any]  # list[RagHit] in-process; list[dict] HTTP mode
    min_score_applied: float  # rag_min_score used (0.0 = no score filter)
    max_chunks_per_doc: int  # per-doc dedup limit applied
