"""rag/cache.py
SemanticCache — in-memory nearest-neighbour embedding cache with dimension validation.

Extracted from rag/repository.py to separate cache concerns from SQL access.
"""

from __future__ import annotations

import logging
from typing import Any, Protocol

from rag.utils import cosine_sim

logger = logging.getLogger(__name__)


class CacheService(Protocol):
    """Protocol for semantic embedding cache implementations."""

    def lookup(self, embedding: list[float]) -> str | None: ...

    def put(self, embedding: list[float], context_str: str) -> None: ...


class SemanticCache:
    """In-memory nearest-neighbour cache; returns context when cosine sim >= threshold, pruned by max_size."""

    def __init__(self, max_size: int = 100, threshold: float = 0.92) -> None:
        self._entries: list[dict[str, Any]] = []  # [{embedding, context_str}]
        self._max_size = max_size
        self._threshold = threshold
        self._dim: int | None = None

    def lookup(self, embedding: list[float]) -> str | None:
        """Return cached context for the nearest embedding, or None on miss.

        Raises ValueError if embedding dimension differs from stored entries.
        """
        if self._dim is not None and len(embedding) != self._dim:
            raise ValueError(
                f"SemanticCache dimension mismatch: expected {self._dim},"
                f" got {len(embedding)}",
            )
        best_sim = -1.0
        best_ctx: str | None = None
        for entry in self._entries:
            sim = cosine_sim(embedding, entry["embedding"])
            if sim > best_sim:
                best_sim = sim
                best_ctx = entry["context_str"]
        if best_sim >= self._threshold:
            logger.debug(f"SemanticCache hit: sim={best_sim:.4f}")
            return best_ctx
        return None

    def put(self, embedding: list[float], context_str: str) -> None:
        """Add a new entry, then prune if over capacity.

        Raises ValueError if embedding dimension differs from previously stored entries.
        """
        if self._dim is None:
            self._dim = len(embedding)
        elif len(embedding) != self._dim:
            raise ValueError(
                f"SemanticCache dimension mismatch: expected {self._dim},"
                f" got {len(embedding)}",
            )
        self._entries.append({"embedding": embedding, "context_str": context_str})
        self.prune()

    def prune(self) -> None:
        """Remove oldest entries when size exceeds max_size."""
        if len(self._entries) > self._max_size:
            self._entries = self._entries[-self._max_size :]

    @property
    def size(self) -> int:
        return len(self._entries)
