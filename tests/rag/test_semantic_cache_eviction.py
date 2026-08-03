"""tests/test_semantic_cache_eviction.py
Verifies that SemanticCache uses FIFO eviction (oldest entry removed first).
"""

from __future__ import annotations

from rag.cache import SemanticCache


def _emb(i: int) -> list[float]:
    """Return a 3-dim embedding with the i-th component set to 1.0 (orthogonal basis)."""
    vec = [0.0, 0.0, 0.0]
    vec[i % 3] = 1.0
    return vec


class TestSemanticCacheFifoEviction:
    def test_oldest_entry_evicted_on_overflow(self) -> None:
        """Put max_size+1 entries; the first entry should be evicted."""
        cache = SemanticCache(max_size=2, threshold=0.5)
        cache.put(_emb(0), "", "result_A")
        cache.put(_emb(1), "", "result_B")
        # Third entry overflows max_size=2; oldest (emb[0]=A) is evicted
        cache.put(_emb(2), "", "result_C")
        # "result_A" should be gone
        assert cache.lookup(_emb(0)) is None
        # "result_B" and "result_C" should still be present
        assert cache.lookup(_emb(1)) is not None
        assert cache.lookup(_emb(2)) is not None

    def test_newest_entry_not_evicted(self) -> None:
        """The most recently inserted entry is never evicted on immediate overflow."""
        cache = SemanticCache(max_size=1, threshold=0.5)
        cache.put(_emb(0), "", "result_A")
        cache.put(_emb(1), "", "result_B")  # evicts A
        assert cache.lookup(_emb(1)) is not None
        assert cache.lookup(_emb(0)) is None

    def test_no_eviction_within_capacity(self) -> None:
        """Entries within max_size are not evicted."""
        cache = SemanticCache(max_size=3, threshold=0.5)
        cache.put(_emb(0), "", "r1")
        cache.put(_emb(1), "", "r2")
        cache.put(_emb(2), "", "r3")
        assert cache.lookup(_emb(0)) is not None
        assert cache.lookup(_emb(1)) is not None
        assert cache.lookup(_emb(2)) is not None

    def test_size_stays_at_max_after_multiple_puts(self) -> None:
        """Cache size never exceeds max_size after repeated puts."""
        cache = SemanticCache(max_size=2, threshold=0.5)
        for i in range(10):
            cache.put(_emb(i), "", f"result_{i}")
        assert cache.size == 2
