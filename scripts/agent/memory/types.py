#!/usr/bin/env python3
"""agent/memory/types.py
Data types for the persistent semantic memory layer.
"""

from __future__ import annotations

from dataclasses import dataclass, field

# Valid values for MemoryEntry.memory_type
MEMORY_TYPES: frozenset[str] = frozenset({"semantic", "episodic"})

# Valid values for MemoryEntry.source_type
SOURCE_TYPES: frozenset[str] = frozenset(
    {"conversation", "decision", "rule", "failure"},
)


@dataclass
class MemoryEntry:
    """One persistent memory unit stored in JSONL and indexed in SQLite."""

    memory_id: str
    memory_type: str  # "semantic" | "episodic"
    source_type: str  # "conversation" | "decision" | "rule" | "failure"
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
    created_at: str = ""  # ISO-8601; filled by MemoryStore.add()
    updated_at: str = ""

    def __post_init__(self) -> None:
        if self.memory_type not in MEMORY_TYPES:
            raise ValueError(
                f"Invalid memory_type={self.memory_type!r}; must be one of {MEMORY_TYPES}",
            )
        if self.source_type not in SOURCE_TYPES:
            raise ValueError(
                f"Invalid source_type={self.source_type!r}; must be one of {SOURCE_TYPES}",
            )
        if not (0.0 <= self.importance <= 1.0):
            raise ValueError(f"importance must be in [0.0, 1.0], got {self.importance}")


@dataclass
class MemoryQuery:
    """Search parameters for memory retrieval."""

    query: str
    session_id: int | None = None
    memory_type: str | None = None  # None = both semantic and episodic
    limit: int = 10


@dataclass
class MemoryHit:
    """One ranked result from memory retrieval."""

    entry: MemoryEntry
    score: float  # combined BM25 + importance + pin + recency score
