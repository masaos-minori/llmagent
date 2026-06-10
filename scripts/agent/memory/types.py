#!/usr/bin/env python3
"""agent/memory/types.py
Data types for the persistent semantic memory layer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum

_ISO8601_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")

# Valid values for MemoryEntry.memory_type
MEMORY_TYPES: frozenset[str] = frozenset({"semantic", "episodic"})


class SourceType(StrEnum):
    """Taxonomy of memory source types.

    StrEnum allows: SourceType.RULE == "rule" → True, enabling comparison
    with string literals without explicit .value access.
    """

    CONVERSATION = "conversation"
    DECISION = "decision"
    RULE = "rule"
    FAILURE = "failure"


class EmbeddingErrorKind(StrEnum):
    """Enumeration of embedding failure reasons.

    StrEnum allows: result.error_kind == "disabled" → True without .value access.
    """

    DISABLED = "disabled"
    CIRCUIT_OPEN = "circuit_open"
    TIMEOUT = "timeout"
    HTTP_ERROR = "http_error"
    INVALID_RESPONSE = "invalid_response"
    UNKNOWN_ERROR = "unknown_error"


@dataclass
class MemoryEntry:
    """One persistent memory unit stored in JSONL and indexed in SQLite."""

    memory_id: str
    memory_type: str  # "semantic" | "episodic"
    source_type: SourceType  # use SourceType enum values
    session_id: int | None
    turn_id: str | None
    project: str
    repo: str
    branch: str
    content: str
    summary: str
    tags: list[str] = field(default_factory=list)
    importance: float = 0.5  # 0.0–1.0; higher = more reuse priority
    pinned: bool = False
    created_at: str = ""  # ISO-8601 UTC; filled by MemoryStore.add()
    updated_at: str = ""

    def __post_init__(self) -> None:
        if self.memory_type not in MEMORY_TYPES:
            raise ValueError(
                f"Invalid memory_type={self.memory_type!r}; must be one of {MEMORY_TYPES}",
            )
        # Coerce string → SourceType; raises ValueError for unknown values.
        if not isinstance(self.source_type, SourceType):
            try:
                object.__setattr__(self, "source_type", SourceType(self.source_type))
            except ValueError:
                raise ValueError(
                    f"Invalid source_type={self.source_type!r}; must be one of {[v.value for v in SourceType]}",
                )
        if not (0.0 <= self.importance <= 1.0):
            raise ValueError(f"importance must be in [0.0, 1.0], got {self.importance}")
        if self.created_at and not _ISO8601_RE.match(self.created_at):
            raise ValueError(
                f"created_at must be ISO-8601 UTC (YYYY-MM-DDTHH:MM:SSZ), got {self.created_at!r}",
            )
        if self.updated_at and not _ISO8601_RE.match(self.updated_at):
            raise ValueError(
                f"updated_at must be ISO-8601 UTC (YYYY-MM-DDTHH:MM:SSZ), got {self.updated_at!r}",
            )


@dataclass
class MemoryQuery:
    """Search parameters for memory retrieval."""

    query: str
    memory_type: str | None = None  # None = both semantic and episodic
    limit: int = 10

    def __post_init__(self) -> None:
        if not self.query.strip():
            raise ValueError("MemoryQuery.query must not be empty")
        if self.memory_type is not None and self.memory_type not in MEMORY_TYPES:
            raise ValueError(
                f"MemoryQuery.memory_type must be 'semantic', 'episodic', or None;"
                f" got {self.memory_type!r}"
            )
        if self.limit < 1:
            raise ValueError(f"MemoryQuery.limit must be >= 1, got {self.limit}")


@dataclass
class MemoryHit:
    """One ranked result from memory retrieval."""

    entry: MemoryEntry
    score: (
        float  # higher is better; FTS: BM25+boosts rescored; KNN: negated L2 distance
    )


@dataclass
class EmbeddingResult:
    """Result of an embedding generation attempt."""

    success: bool
    embedding: list[float] | None = None
    error_kind: EmbeddingErrorKind | None = None
