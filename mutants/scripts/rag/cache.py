"""scripts/rag/cache.py

SemanticCache — in-memory nearest-neighbour embedding cache with dimension validation.

Extracted from rag/repository.py to separate cache concerns from SQL access.
"""

from __future__ import annotations

import logging
import threading
from typing import Protocol

from rag.models_data import CacheEntry
from rag.utils import cosine_sim

logger = logging.getLogger(__name__)


from mutmut.mutation.trampoline import wrap_in_trampoline as _mutmut_mutated, MutantDict
mutants_xǁCacheServiceǁlookup__mutmut: MutantDict = {}  # type: ignore


class CacheService(Protocol):
    """Protocol for semantic embedding cache implementations."""

    @_mutmut_mutated(mutants_xǁCacheServiceǁlookup__mutmut)
    def lookup(self, embedding: list[float], history_context: str = "") -> str | None:
        """Look up a cached context by embedding similarity."""
        ...

    def xǁCacheServiceǁlookup__mutmut_orig(self, embedding: list[float], history_context: str = "") -> str | None:
        """Look up a cached context by embedding similarity."""
        ...

    def xǁCacheServiceǁlookup__mutmut_1(self, embedding: list[float], history_context: str = "XXXX") -> str | None:
        """Look up a cached context by embedding similarity."""
        ...

    def put(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        ...

mutants_xǁCacheServiceǁlookup__mutmut['_mutmut_orig'] = CacheService.xǁCacheServiceǁlookup__mutmut_orig # type: ignore # mutmut generated
mutants_xǁCacheServiceǁlookup__mutmut['xǁCacheServiceǁlookup__mutmut_1'] = CacheService.xǁCacheServiceǁlookup__mutmut_1 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁ__init____mutmut: MutantDict = {}  # type: ignore
mutants_xǁSemanticCacheǁlookup__mutmut: MutantDict = {}  # type: ignore
mutants_xǁSemanticCacheǁput__mutmut: MutantDict = {}  # type: ignore
mutants_xǁSemanticCacheǁprune__mutmut: MutantDict = {}  # type: ignore
mutants_xǁSemanticCacheǁinvalidate__mutmut: MutantDict = {}  # type: ignore


class SemanticCache:
    """In-memory nearest-neighbour cache with FIFO eviction (oldest entry removed first when size > max_size)."""

    @_mutmut_mutated(mutants_xǁSemanticCacheǁ__init____mutmut)
    def __init__(self, max_size: int = 100, threshold: float = 0.92) -> None:
        """Initialize with maximum cache size and similarity threshold."""
        self._entries: list[CacheEntry] = []
        self._max_size = max_size
        self._threshold = threshold
        self._dim: int | None = None
        self._lock: threading.RLock = threading.RLock()
        self._generation: int = 0

    def xǁSemanticCacheǁ__init____mutmut_orig(self, max_size: int = 100, threshold: float = 0.92) -> None:
        """Initialize with maximum cache size and similarity threshold."""
        self._entries: list[CacheEntry] = []
        self._max_size = max_size
        self._threshold = threshold
        self._dim: int | None = None
        self._lock: threading.RLock = threading.RLock()
        self._generation: int = 0

    def xǁSemanticCacheǁ__init____mutmut_1(self, max_size: int = 101, threshold: float = 0.92) -> None:
        """Initialize with maximum cache size and similarity threshold."""
        self._entries: list[CacheEntry] = []
        self._max_size = max_size
        self._threshold = threshold
        self._dim: int | None = None
        self._lock: threading.RLock = threading.RLock()
        self._generation: int = 0

    def xǁSemanticCacheǁ__init____mutmut_2(self, max_size: int = 100, threshold: float = 1.92) -> None:
        """Initialize with maximum cache size and similarity threshold."""
        self._entries: list[CacheEntry] = []
        self._max_size = max_size
        self._threshold = threshold
        self._dim: int | None = None
        self._lock: threading.RLock = threading.RLock()
        self._generation: int = 0

    def xǁSemanticCacheǁ__init____mutmut_3(self, max_size: int = 100, threshold: float = 0.92) -> None:
        """Initialize with maximum cache size and similarity threshold."""
        self._entries: list[CacheEntry] = None
        self._max_size = max_size
        self._threshold = threshold
        self._dim: int | None = None
        self._lock: threading.RLock = threading.RLock()
        self._generation: int = 0

    def xǁSemanticCacheǁ__init____mutmut_4(self, max_size: int = 100, threshold: float = 0.92) -> None:
        """Initialize with maximum cache size and similarity threshold."""
        self._entries: list[CacheEntry] = []
        self._max_size = None
        self._threshold = threshold
        self._dim: int | None = None
        self._lock: threading.RLock = threading.RLock()
        self._generation: int = 0

    def xǁSemanticCacheǁ__init____mutmut_5(self, max_size: int = 100, threshold: float = 0.92) -> None:
        """Initialize with maximum cache size and similarity threshold."""
        self._entries: list[CacheEntry] = []
        self._max_size = max_size
        self._threshold = None
        self._dim: int | None = None
        self._lock: threading.RLock = threading.RLock()
        self._generation: int = 0

    def xǁSemanticCacheǁ__init____mutmut_6(self, max_size: int = 100, threshold: float = 0.92) -> None:
        """Initialize with maximum cache size and similarity threshold."""
        self._entries: list[CacheEntry] = []
        self._max_size = max_size
        self._threshold = threshold
        self._dim: int | None = ""
        self._lock: threading.RLock = threading.RLock()
        self._generation: int = 0

    def xǁSemanticCacheǁ__init____mutmut_7(self, max_size: int = 100, threshold: float = 0.92) -> None:
        """Initialize with maximum cache size and similarity threshold."""
        self._entries: list[CacheEntry] = []
        self._max_size = max_size
        self._threshold = threshold
        self._dim: int | None = None
        self._lock: threading.RLock = None
        self._generation: int = 0

    def xǁSemanticCacheǁ__init____mutmut_8(self, max_size: int = 100, threshold: float = 0.92) -> None:
        """Initialize with maximum cache size and similarity threshold."""
        self._entries: list[CacheEntry] = []
        self._max_size = max_size
        self._threshold = threshold
        self._dim: int | None = None
        self._lock: threading.RLock = threading.RLock()
        self._generation: int = None

    def xǁSemanticCacheǁ__init____mutmut_9(self, max_size: int = 100, threshold: float = 0.92) -> None:
        """Initialize with maximum cache size and similarity threshold."""
        self._entries: list[CacheEntry] = []
        self._max_size = max_size
        self._threshold = threshold
        self._dim: int | None = None
        self._lock: threading.RLock = threading.RLock()
        self._generation: int = 1

    @_mutmut_mutated(mutants_xǁSemanticCacheǁlookup__mutmut)
    def lookup(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_orig(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_1(self, embedding: list[float], history_context: str = "XXXX") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_2(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None or len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_3(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_4(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) == self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_5(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    None,
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_6(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    None,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_7(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    None,
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_8(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_9(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_10(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_11(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "XXSemanticCache dimension mismatch: expected %d, got %dXX",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_12(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "semanticcache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_13(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SEMANTICCACHE DIMENSION MISMATCH: EXPECTED %D, GOT %D",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_14(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = None
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_15(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = +1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_16(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -2.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_17(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = ""
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_18(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context == history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_19(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    break
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_20(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = None
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_21(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(None, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_22(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, None)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_23(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_24(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, )
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_25(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim >= best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_26(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = None
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_27(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = None
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_28(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim > self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_29(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug(None, best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_30(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", None)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_31(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug(best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_32(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SemanticCache hit: sim=%.4f", )
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_33(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("XXSemanticCache hit: sim=%.4fXX", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_34(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("semanticcache hit: sim=%.4f", best_sim)
                return best_ctx
            return None

    def xǁSemanticCacheǁlookup__mutmut_35(self, embedding: list[float], history_context: str = "") -> str | None:
        """Return cached context for the nearest embedding with matching history_context, or None on miss.

        Returns None if embedding dimension differs from stored entries (treated as cache miss).
        """
        with self._lock:
            if self._dim is not None and len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return None  # Treat as cache miss
            best_sim = -1.0
            best_ctx: str | None = None
            for entry in self._entries:
                if entry.history_context != history_context:
                    continue
                sim = cosine_sim(embedding, entry.embedding)
                if sim > best_sim:
                    best_sim = sim
                    best_ctx = entry.context_str
            if best_sim >= self._threshold:
                logger.debug("SEMANTICCACHE HIT: SIM=%.4F", best_sim)
                return best_ctx
            return None

    @_mutmut_mutated(mutants_xǁSemanticCacheǁput__mutmut)
    def put(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch during put: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    context_str=context_str,
                    history_context=history_context,
                    generation=self._generation,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_orig(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch during put: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    context_str=context_str,
                    history_context=history_context,
                    generation=self._generation,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_1(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is not None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch during put: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    context_str=context_str,
                    history_context=history_context,
                    generation=self._generation,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_2(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = None
            elif len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch during put: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    context_str=context_str,
                    history_context=history_context,
                    generation=self._generation,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_3(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) == self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch during put: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    context_str=context_str,
                    history_context=history_context,
                    generation=self._generation,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_4(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    None,
                    self._dim,
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    context_str=context_str,
                    history_context=history_context,
                    generation=self._generation,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_5(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch during put: expected %d, got %d",
                    None,
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    context_str=context_str,
                    history_context=history_context,
                    generation=self._generation,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_6(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch during put: expected %d, got %d",
                    self._dim,
                    None,
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    context_str=context_str,
                    history_context=history_context,
                    generation=self._generation,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_7(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    self._dim,
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    context_str=context_str,
                    history_context=history_context,
                    generation=self._generation,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_8(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch during put: expected %d, got %d",
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    context_str=context_str,
                    history_context=history_context,
                    generation=self._generation,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_9(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch during put: expected %d, got %d",
                    self._dim,
                    )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    context_str=context_str,
                    history_context=history_context,
                    generation=self._generation,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_10(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    "XXSemanticCache dimension mismatch during put: expected %d, got %dXX",
                    self._dim,
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    context_str=context_str,
                    history_context=history_context,
                    generation=self._generation,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_11(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    "semanticcache dimension mismatch during put: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    context_str=context_str,
                    history_context=history_context,
                    generation=self._generation,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_12(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    "SEMANTICCACHE DIMENSION MISMATCH DURING PUT: EXPECTED %D, GOT %D",
                    self._dim,
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    context_str=context_str,
                    history_context=history_context,
                    generation=self._generation,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_13(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch during put: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return True  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    context_str=context_str,
                    history_context=history_context,
                    generation=self._generation,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_14(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch during put: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                None
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_15(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch during put: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=None,
                    context_str=context_str,
                    history_context=history_context,
                    generation=self._generation,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_16(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch during put: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    context_str=None,
                    history_context=history_context,
                    generation=self._generation,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_17(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch during put: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    context_str=context_str,
                    history_context=None,
                    generation=self._generation,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_18(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch during put: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    context_str=context_str,
                    history_context=history_context,
                    generation=None,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_19(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch during put: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    context_str=context_str,
                    history_context=history_context,
                    generation=self._generation,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_20(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch during put: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    history_context=history_context,
                    generation=self._generation,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_21(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch during put: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    context_str=context_str,
                    generation=self._generation,
                )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_22(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch during put: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    context_str=context_str,
                    history_context=history_context,
                    )
            )
            self.prune()
            return True

    def xǁSemanticCacheǁput__mutmut_23(
        self, embedding: list[float], history_context: str, context_str: str
    ) -> bool:
        """Store an embedding-context pair in the cache.

        Returns True on success, False if dimension mismatch prevents insertion.
        """
        with self._lock:
            if self._dim is None:
                self._dim = len(embedding)
            elif len(embedding) != self._dim:
                logger.warning(
                    "SemanticCache dimension mismatch during put: expected %d, got %d",
                    self._dim,
                    len(embedding),
                )
                return False  # Don't insert incompatible entry
            self._entries.append(
                CacheEntry(
                    embedding=embedding,
                    context_str=context_str,
                    history_context=history_context,
                    generation=self._generation,
                )
            )
            self.prune()
            return False

    @_mutmut_mutated(mutants_xǁSemanticCacheǁprune__mutmut)
    def prune(self) -> None:
        """Remove oldest entries (FIFO) when len(self._entries) > max_size.

        When max_size <= 0, the cache holds zero entries (capacity zero).
        """
        with self._lock:
            if self._max_size <= 0:
                self._entries = []
            elif len(self._entries) > self._max_size:
                self._entries = self._entries[-self._max_size :]

    def xǁSemanticCacheǁprune__mutmut_orig(self) -> None:
        """Remove oldest entries (FIFO) when len(self._entries) > max_size.

        When max_size <= 0, the cache holds zero entries (capacity zero).
        """
        with self._lock:
            if self._max_size <= 0:
                self._entries = []
            elif len(self._entries) > self._max_size:
                self._entries = self._entries[-self._max_size :]

    def xǁSemanticCacheǁprune__mutmut_1(self) -> None:
        """Remove oldest entries (FIFO) when len(self._entries) > max_size.

        When max_size <= 0, the cache holds zero entries (capacity zero).
        """
        with self._lock:
            if self._max_size < 0:
                self._entries = []
            elif len(self._entries) > self._max_size:
                self._entries = self._entries[-self._max_size :]

    def xǁSemanticCacheǁprune__mutmut_2(self) -> None:
        """Remove oldest entries (FIFO) when len(self._entries) > max_size.

        When max_size <= 0, the cache holds zero entries (capacity zero).
        """
        with self._lock:
            if self._max_size <= 1:
                self._entries = []
            elif len(self._entries) > self._max_size:
                self._entries = self._entries[-self._max_size :]

    def xǁSemanticCacheǁprune__mutmut_3(self) -> None:
        """Remove oldest entries (FIFO) when len(self._entries) > max_size.

        When max_size <= 0, the cache holds zero entries (capacity zero).
        """
        with self._lock:
            if self._max_size <= 0:
                self._entries = None
            elif len(self._entries) > self._max_size:
                self._entries = self._entries[-self._max_size :]

    def xǁSemanticCacheǁprune__mutmut_4(self) -> None:
        """Remove oldest entries (FIFO) when len(self._entries) > max_size.

        When max_size <= 0, the cache holds zero entries (capacity zero).
        """
        with self._lock:
            if self._max_size <= 0:
                self._entries = []
            elif len(self._entries) >= self._max_size:
                self._entries = self._entries[-self._max_size :]

    def xǁSemanticCacheǁprune__mutmut_5(self) -> None:
        """Remove oldest entries (FIFO) when len(self._entries) > max_size.

        When max_size <= 0, the cache holds zero entries (capacity zero).
        """
        with self._lock:
            if self._max_size <= 0:
                self._entries = []
            elif len(self._entries) > self._max_size:
                self._entries = None

    def xǁSemanticCacheǁprune__mutmut_6(self) -> None:
        """Remove oldest entries (FIFO) when len(self._entries) > max_size.

        When max_size <= 0, the cache holds zero entries (capacity zero).
        """
        with self._lock:
            if self._max_size <= 0:
                self._entries = []
            elif len(self._entries) > self._max_size:
                self._entries = self._entries[+self._max_size :]

    @property
    def size(self) -> int:
        """Return the current number of cached entries."""
        with self._lock:
            return len(self._entries)

    @_mutmut_mutated(mutants_xǁSemanticCacheǁinvalidate__mutmut)
    def invalidate(self) -> None:
        """Bump generation; clear all cached entries atomically."""
        with self._lock:
            self._generation += 1
            self._entries.clear()

    def xǁSemanticCacheǁinvalidate__mutmut_orig(self) -> None:
        """Bump generation; clear all cached entries atomically."""
        with self._lock:
            self._generation += 1
            self._entries.clear()

    def xǁSemanticCacheǁinvalidate__mutmut_1(self) -> None:
        """Bump generation; clear all cached entries atomically."""
        with self._lock:
            self._generation = 1
            self._entries.clear()

    def xǁSemanticCacheǁinvalidate__mutmut_2(self) -> None:
        """Bump generation; clear all cached entries atomically."""
        with self._lock:
            self._generation -= 1
            self._entries.clear()

    def xǁSemanticCacheǁinvalidate__mutmut_3(self) -> None:
        """Bump generation; clear all cached entries atomically."""
        with self._lock:
            self._generation += 2
            self._entries.clear()

    @property
    def generation(self) -> int:
        """Return the current generation counter."""
        with self._lock:
            return self._generation

mutants_xǁSemanticCacheǁ__init____mutmut['_mutmut_orig'] = SemanticCache.xǁSemanticCacheǁ__init____mutmut_orig # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁ__init____mutmut['xǁSemanticCacheǁ__init____mutmut_1'] = SemanticCache.xǁSemanticCacheǁ__init____mutmut_1 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁ__init____mutmut['xǁSemanticCacheǁ__init____mutmut_2'] = SemanticCache.xǁSemanticCacheǁ__init____mutmut_2 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁ__init____mutmut['xǁSemanticCacheǁ__init____mutmut_3'] = SemanticCache.xǁSemanticCacheǁ__init____mutmut_3 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁ__init____mutmut['xǁSemanticCacheǁ__init____mutmut_4'] = SemanticCache.xǁSemanticCacheǁ__init____mutmut_4 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁ__init____mutmut['xǁSemanticCacheǁ__init____mutmut_5'] = SemanticCache.xǁSemanticCacheǁ__init____mutmut_5 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁ__init____mutmut['xǁSemanticCacheǁ__init____mutmut_6'] = SemanticCache.xǁSemanticCacheǁ__init____mutmut_6 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁ__init____mutmut['xǁSemanticCacheǁ__init____mutmut_7'] = SemanticCache.xǁSemanticCacheǁ__init____mutmut_7 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁ__init____mutmut['xǁSemanticCacheǁ__init____mutmut_8'] = SemanticCache.xǁSemanticCacheǁ__init____mutmut_8 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁ__init____mutmut['xǁSemanticCacheǁ__init____mutmut_9'] = SemanticCache.xǁSemanticCacheǁ__init____mutmut_9 # type: ignore # mutmut generated

mutants_xǁSemanticCacheǁlookup__mutmut['_mutmut_orig'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_orig # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_1'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_1 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_2'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_2 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_3'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_3 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_4'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_4 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_5'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_5 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_6'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_6 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_7'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_7 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_8'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_8 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_9'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_9 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_10'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_10 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_11'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_11 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_12'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_12 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_13'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_13 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_14'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_14 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_15'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_15 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_16'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_16 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_17'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_17 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_18'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_18 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_19'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_19 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_20'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_20 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_21'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_21 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_22'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_22 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_23'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_23 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_24'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_24 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_25'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_25 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_26'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_26 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_27'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_27 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_28'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_28 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_29'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_29 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_30'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_30 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_31'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_31 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_32'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_32 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_33'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_33 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_34'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_34 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁlookup__mutmut['xǁSemanticCacheǁlookup__mutmut_35'] = SemanticCache.xǁSemanticCacheǁlookup__mutmut_35 # type: ignore # mutmut generated

mutants_xǁSemanticCacheǁput__mutmut['_mutmut_orig'] = SemanticCache.xǁSemanticCacheǁput__mutmut_orig # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_1'] = SemanticCache.xǁSemanticCacheǁput__mutmut_1 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_2'] = SemanticCache.xǁSemanticCacheǁput__mutmut_2 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_3'] = SemanticCache.xǁSemanticCacheǁput__mutmut_3 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_4'] = SemanticCache.xǁSemanticCacheǁput__mutmut_4 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_5'] = SemanticCache.xǁSemanticCacheǁput__mutmut_5 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_6'] = SemanticCache.xǁSemanticCacheǁput__mutmut_6 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_7'] = SemanticCache.xǁSemanticCacheǁput__mutmut_7 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_8'] = SemanticCache.xǁSemanticCacheǁput__mutmut_8 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_9'] = SemanticCache.xǁSemanticCacheǁput__mutmut_9 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_10'] = SemanticCache.xǁSemanticCacheǁput__mutmut_10 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_11'] = SemanticCache.xǁSemanticCacheǁput__mutmut_11 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_12'] = SemanticCache.xǁSemanticCacheǁput__mutmut_12 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_13'] = SemanticCache.xǁSemanticCacheǁput__mutmut_13 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_14'] = SemanticCache.xǁSemanticCacheǁput__mutmut_14 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_15'] = SemanticCache.xǁSemanticCacheǁput__mutmut_15 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_16'] = SemanticCache.xǁSemanticCacheǁput__mutmut_16 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_17'] = SemanticCache.xǁSemanticCacheǁput__mutmut_17 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_18'] = SemanticCache.xǁSemanticCacheǁput__mutmut_18 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_19'] = SemanticCache.xǁSemanticCacheǁput__mutmut_19 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_20'] = SemanticCache.xǁSemanticCacheǁput__mutmut_20 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_21'] = SemanticCache.xǁSemanticCacheǁput__mutmut_21 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_22'] = SemanticCache.xǁSemanticCacheǁput__mutmut_22 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁput__mutmut['xǁSemanticCacheǁput__mutmut_23'] = SemanticCache.xǁSemanticCacheǁput__mutmut_23 # type: ignore # mutmut generated

mutants_xǁSemanticCacheǁprune__mutmut['_mutmut_orig'] = SemanticCache.xǁSemanticCacheǁprune__mutmut_orig # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁprune__mutmut['xǁSemanticCacheǁprune__mutmut_1'] = SemanticCache.xǁSemanticCacheǁprune__mutmut_1 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁprune__mutmut['xǁSemanticCacheǁprune__mutmut_2'] = SemanticCache.xǁSemanticCacheǁprune__mutmut_2 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁprune__mutmut['xǁSemanticCacheǁprune__mutmut_3'] = SemanticCache.xǁSemanticCacheǁprune__mutmut_3 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁprune__mutmut['xǁSemanticCacheǁprune__mutmut_4'] = SemanticCache.xǁSemanticCacheǁprune__mutmut_4 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁprune__mutmut['xǁSemanticCacheǁprune__mutmut_5'] = SemanticCache.xǁSemanticCacheǁprune__mutmut_5 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁprune__mutmut['xǁSemanticCacheǁprune__mutmut_6'] = SemanticCache.xǁSemanticCacheǁprune__mutmut_6 # type: ignore # mutmut generated

mutants_xǁSemanticCacheǁinvalidate__mutmut['_mutmut_orig'] = SemanticCache.xǁSemanticCacheǁinvalidate__mutmut_orig # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁinvalidate__mutmut['xǁSemanticCacheǁinvalidate__mutmut_1'] = SemanticCache.xǁSemanticCacheǁinvalidate__mutmut_1 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁinvalidate__mutmut['xǁSemanticCacheǁinvalidate__mutmut_2'] = SemanticCache.xǁSemanticCacheǁinvalidate__mutmut_2 # type: ignore # mutmut generated
mutants_xǁSemanticCacheǁinvalidate__mutmut['xǁSemanticCacheǁinvalidate__mutmut_3'] = SemanticCache.xǁSemanticCacheǁinvalidate__mutmut_3 # type: ignore # mutmut generated
