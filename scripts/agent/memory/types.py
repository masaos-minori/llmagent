#!/usr/bin/env python3
"""agent/memory/types.py

Data types for the persistent semantic memory layer.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TypeVar, cast

from agent.memory.enums import MemoryType

T = TypeVar("T", bound=StrEnum)


def _coerce_str_enum(value: object, enum_cls: type[StrEnum]) -> StrEnum:
    """Coerce a value to an enum if it is a string; raise ValueError otherwise."""
    if isinstance(value, enum_cls):
        return value
    if not isinstance(value, str):
        raise ValueError(
            f"Expected {enum_cls.__name__} or None, got {type(value).__name__}"
        )
    try:
        return enum_cls(value)
    except ValueError:
        raise ValueError(
            f"{enum_cls.__name__} must be one of {[m.value for m in enum_cls]}; got {value!r}"
        )


def _coerce_str_enum_or_none(
    value: object | None, enum_cls: type[StrEnum]
) -> StrEnum | None:
    """Coerce a value to an enum if it is a string; return None if value is None."""
    if value is None:
        return None
    return _coerce_str_enum(value, enum_cls)


_ISO8601_RE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _validate_iso8601(value: str, field: str) -> None:
    """Raise ValueError if value is non-empty and not ISO-8601 UTC format."""
    if value and not _ISO8601_RE.match(value):
        raise ValueError(
            f"{field} must be ISO-8601 UTC (YYYY-MM-DDTHH:MM:SSZ), got {value!r}",
        )


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
    DIMENSION_MISMATCH = "dimension_mismatch"


@dataclass(frozen=True)
class MemoryEntry:
    """One persistent memory unit stored in JSONL and indexed in SQLite."""

    memory_id: str
    memory_type: MemoryType
    source_type: SourceType
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
        """Coerce enum fields and validate importance range after dataclass initialization."""
        coerced_memory_type = cast(
            MemoryType, _coerce_str_enum(self.memory_type, MemoryType)
        )
        object.__setattr__(self, "memory_type", coerced_memory_type)
        coerced_source_type = cast(
            SourceType, _coerce_str_enum(self.source_type, SourceType)
        )
        object.__setattr__(self, "source_type", coerced_source_type)
        if not (0.0 <= self.importance <= 1.0):
            raise ValueError(f"importance must be in [0.0, 1.0], got {self.importance}")
        _validate_iso8601(self.created_at, "created_at")
        _validate_iso8601(self.updated_at, "updated_at")


@dataclass
class MemoryQuery:
    """Search parameters for memory retrieval."""

    query: str
    memory_type: MemoryType | None = None  # None = both semantic and episodic
    limit: int = 10
    session_id: int | None = None

    def __post_init__(self) -> None:
        """Validate query non-emptyness and coerce optional memory type after dataclass initialization."""
        if not self.query.strip():
            raise ValueError("MemoryQuery.query must not be empty")
        coerced = _coerce_str_enum_or_none(self.memory_type, MemoryType)
        object.__setattr__(self, "memory_type", cast(MemoryType | None, coerced))
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
