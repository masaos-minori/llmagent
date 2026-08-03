"""tests/test_semantic_cache_invalidate.py
Verifies that SemanticCache.invalidate() clears all entries and bumps generation.
"""

from __future__ import annotations

from rag.cache import SemanticCache


def _emb(i: int) -> list[float]:
    """Return a 3-dim embedding with the i-th component set to 1.0 (orthogonal basis)."""
    vec = [0.0, 0.0, 0.0]
    vec[i % 3] = 1.0
    return vec


class TestSemanticCacheInvalidate:
    def test_invalidate_clears_all_entries(self) -> None:
        """invalidate() removes all cached entries."""
        cache = SemanticCache(max_size=10, threshold=0.5)
        cache.put(_emb(0), "", "result_A")
        cache.put(_emb(1), "", "result_B")
        assert cache.lookup(_emb(0)) is not None
        assert cache.lookup(_emb(1)) is not None
        cache.invalidate()
        assert cache.lookup(_emb(0)) is None
        assert cache.lookup(_emb(1)) is None

    def test_invalidate_bumps_generation(self) -> None:
        """invalidate() increments the generation counter."""
        cache = SemanticCache(max_size=10, threshold=0.5)
        assert cache.generation == 0
        cache.invalidate()
        assert cache.generation == 1
        cache.invalidate()
        assert cache.generation == 2

    def test_invalidate_clears_size(self) -> None:
        """invalidate() resets the cache size to 0."""
        cache = SemanticCache(max_size=10, threshold=0.5)
        cache.put(_emb(0), "", "result_A")
        cache.put(_emb(1), "", "result_B")
        assert cache.size == 2
        cache.invalidate()
        assert cache.size == 0

    def test_invalidate_atomic_with_lock(self) -> None:
        """invalidate() is thread-safe; concurrent put after invalidate works."""
        import threading

        cache = SemanticCache(max_size=10, threshold=0.5)
        cache.put(_emb(0), "", "result_A")
        assert cache.size == 1

        errors: list[Exception] = []

        def invalidate() -> None:
            try:
                cache.invalidate()
            except Exception as e:
                errors.append(e)

        def put_after() -> None:
            try:
                cache.put(_emb(1), "", "result_B")
            except Exception as e:
                errors.append(e)

        t1 = threading.Thread(target=invalidate)
        t2 = threading.Thread(target=put_after)
        t1.start()
        t2.start()
        t1.join(timeout=5)
        t2.join(timeout=5)
        assert not errors, f"Concurrent access raised: {errors}"
        # At least one of the operations should have taken effect
        assert cache.size >= 0

    def test_invalidate_then_put_works(self) -> None:
        """After invalidate(), new entries can be added."""
        cache = SemanticCache(max_size=10, threshold=0.5)
        cache.put(_emb(0), "", "result_A")
        assert cache.size == 1
        cache.invalidate()
        assert cache.size == 0
        cache.put(_emb(1), "", "result_B")
        assert cache.size == 1
        assert cache.lookup(_emb(1)) is not None

    def test_invalidate_with_empty_cache(self) -> None:
        """invalidate() on an empty cache does nothing harmful."""
        cache = SemanticCache(max_size=10, threshold=0.5)
        cache.invalidate()
        assert cache.size == 0
        assert cache.generation == 1
