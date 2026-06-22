"""tests/test_semantic_cache_concurrency.py
Thread-safety regression tests for SemanticCache._lock (threading.RLock).
"""

from __future__ import annotations

import threading

from rag.cache import SemanticCache

_DIM = 4
_THREADS = 5


def _vec(v: float) -> list[float]:
    return [v] * _DIM


class TestSemanticCacheConcurrency:
    def test_concurrent_lookups_no_crash(self) -> None:
        cache = SemanticCache(max_size=100, threshold=0.99)
        cache.put(_vec(1.0), "", "ctx")
        errors: list[Exception] = []
        barrier = threading.Barrier(_THREADS)

        def _lookup() -> None:
            barrier.wait()
            try:
                cache.lookup(_vec(1.0))
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=_lookup) for _ in range(_THREADS)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []

    def test_concurrent_puts_no_data_loss(self) -> None:
        cache = SemanticCache(max_size=_THREADS + 10, threshold=0.0)
        errors: list[Exception] = []
        barrier = threading.Barrier(_THREADS)

        def _put(i: int) -> None:
            barrier.wait()
            try:
                cache.put(_vec(float(i) / _THREADS), "", f"ctx{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=_put, args=(i,)) for i in range(_THREADS)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []
        assert cache.size == _THREADS

    def test_concurrent_put_and_lookup_consistent(self) -> None:
        cache = SemanticCache(max_size=200, threshold=0.99)
        errors: list[Exception] = []
        barrier = threading.Barrier(_THREADS * 2)

        def _put(i: int) -> None:
            barrier.wait()
            try:
                cache.put(_vec(float(i) / _THREADS), "", f"ctx{i}")
            except Exception as e:
                errors.append(e)

        def _lookup() -> None:
            barrier.wait()
            try:
                cache.lookup(_vec(0.5))
            except Exception as e:
                errors.append(e)

        threads = [
            threading.Thread(target=_put, args=(i,)) for i in range(_THREADS)
        ] + [threading.Thread(target=_lookup) for _ in range(_THREADS)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []

    def test_prune_under_concurrent_access(self) -> None:
        cache = SemanticCache(max_size=10, threshold=0.0)
        errors: list[Exception] = []
        barrier = threading.Barrier(_THREADS)

        def _work(i: int) -> None:
            barrier.wait()
            try:
                cache.put(_vec(float(i) / _THREADS), "", f"ctx{i}")
                cache.lookup(_vec(float(i) / _THREADS))
                cache.prune()
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=_work, args=(i,)) for i in range(_THREADS)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert errors == []
        assert cache.size <= 10
