"""tests/test_rag_cache.py

Tests for SemanticCache behavior: zero/negative capacity, FIFO pruning,
invalidation, history-context separation, dimension mismatch, lock re-entrancy.
"""

from __future__ import annotations

import pytest
from rag.cache import SemanticCache


def _emb(dim: int, idx: int) -> list[float]:
    """Return a dim-dimensional embedding with the idx-th component set to 1.0."""
    vec = [0.0] * dim
    vec[idx % dim] = 1.0
    return vec


class TestSemanticCacheCapacityZero:
    def test_max_size_zero_keeps_no_entries(self) -> None:
        """Put several entries into a zero-capacity cache; size must stay 0 after each put()."""
        cache = SemanticCache(max_size=0, threshold=0.0)
        cache.put(_emb(3, 0), "", "result_A")
        assert cache.size == 0
        cache.put(_emb(3, 1), "", "result_B")
        assert cache.size == 0
        cache.put(_emb(3, 2), "", "result_C")
        assert cache.size == 0

    def test_negative_max_size_does_not_grow_unbounded(self) -> None:
        """Negative max_size must also yield a zero-capacity cache."""
        cache = SemanticCache(max_size=-5, threshold=0.0)
        cache.put(_emb(3, 0), "", "result_A")
        assert cache.size == 0
        cache.put(_emb(3, 1), "", "result_B")
        assert cache.size == 0
        cache.put(_emb(3, 2), "", "result_C")
        assert cache.size == 0


class TestSemanticCachePruning:
    def test_fifo_pruning_normal(self) -> None:
        """Put 3 entries into a cache with max_size=2; only the last 2 remain."""
        cache = SemanticCache(max_size=2, threshold=0.5)
        cache.put(_emb(3, 0), "", "result_A")
        cache.put(_emb(3, 1), "", "result_B")
        # Third entry overflows max_size=2; oldest (emb[0]=A) is evicted
        cache.put(_emb(3, 2), "", "result_C")
        assert cache.size == 2
        assert cache.lookup(_emb(3, 0)) is None
        assert cache.lookup(_emb(3, 1)) == "result_B"
        assert cache.lookup(_emb(3, 2)) == "result_C"


class TestSemanticCacheInvalidate:
    def test_invalidate_clears_entries_and_bumps_generation(self) -> None:
        """invalidate() clears all entries and increments generation by 1."""
        cache = SemanticCache(max_size=10, threshold=0.0)
        cache.put(_emb(3, 0), "", "result_A")
        gen_before = cache.generation
        cache.invalidate()
        assert cache.size == 0
        assert cache.generation == gen_before + 1


class TestSemanticCacheHistoryContext:
    def test_history_context_separation(self) -> None:
        """Same embedding but different history_context values must return distinct results."""
        cache = SemanticCache(max_size=10, threshold=0.0)
        emb = _emb(3, 0)
        cache.put(emb, "session-a", "result_a")
        cache.put(emb, "session-b", "result_b")
        assert cache.lookup(emb, history_context="session-a") == "result_a"
        assert cache.lookup(emb, history_context="session-b") == "result_b"


class TestSemanticCacheDimensionMismatch:
    def test_embedding_dimension_mismatch_raises(self) -> None:
        """put()/lookup() with a different dimension than established must raise ValueError."""
        cache = SemanticCache(max_size=10, threshold=0.0)
        cache.put([1.0], "", "result_a")  # establishes dim=1
        with pytest.raises(ValueError):
            cache.put([1.0, 0.0], "", "result_b")  # dim=2 mismatch

        cache2 = SemanticCache(max_size=10, threshold=0.0)
        cache2.put([1.0], "", "result_a")  # establishes dim=1
        with pytest.raises(ValueError):
            cache2.lookup([1.0, 0.0])  # lookup dim=2 mismatch


class TestSemanticCacheLockReEntrancy:
    def test_size_and_generation_readable_without_lock_deadlock(self) -> None:
        """Reading size/generation immediately after a mutating method must not deadlock."""
        cache = SemanticCache(max_size=10, threshold=0.0)
        cache.put(_emb(3, 0), "", "result_a")
        size = cache.size
        gen_before = cache.generation
        assert size == 1
        assert gen_before == 0

        cache.invalidate()
        size_after = cache.size
        gen_after = cache.generation
        assert size_after == 0
        assert gen_after > gen_before
