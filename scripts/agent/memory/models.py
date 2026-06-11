"""agent/memory/models.py
Frozen dataclass DTOs for the persistent memory layer.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class HistoryMessage:
    """Memory-local representation of one conversation message."""

    role: str
    content: str


@dataclass(frozen=True)
class JsonlRecord:
    """One deserialized record from the JSONL memory store."""

    memory_id: str
    memory_type: str
    source_type: str
    session_id: int | None
    turn_id: str | None
    project: str
    repo: str
    branch: str
    content: str
    summary: str
    tags: list[str]
    importance: float
    pinned: bool
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class ConsistencyReport:
    """Row counts across memories / memories_fts / memories_vec tables."""

    memories: int
    fts: int
    vec: int


@dataclass(frozen=True)
class EmbeddingRequest:
    """Input to the embedding service."""

    text: str
    query_prefix: str


@dataclass(frozen=True)
class EmbeddingResponse:
    """Validated response from the embedding service."""

    embedding: list[float]
    model: str | None = None


@dataclass(frozen=True)
class InjectionSnippet:
    """One memory snippet to inject into the LLM context."""

    prefix: str
    text: str
    memory_id: str
    memory_type: str
