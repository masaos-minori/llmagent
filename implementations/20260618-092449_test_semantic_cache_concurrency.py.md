# Implementation: tests/test_semantic_cache_concurrency.py

## Goal

Create concurrency regression tests that verify `SemanticCache` is safe under concurrent access: no crashes, no data loss, no corrupted state when multiple threads call `lookup()`, `put()`, and `prune()` simultaneously.

## Scope

- New file: `tests/test_semantic_cache_concurrency.py`
- No production code changes.

## Assumptions

1. `SemanticCache` uses `threading.RLock` after the `cache.py` implementation step completes.
2. Tests use `threading.Thread` (not asyncio) since concurrency protection is thread-based.
3. A 4-dimensional embedding is sufficient for test clarity.
4. 50 concurrent threads is sufficient to expose race conditions reliably without test flakiness.
5. `SemanticCache.size` property (line 91) gives the current entry count.

## Implementation

### Target file

`tests/test_semantic_cache_concurrency.py`

### Procedure

1. Write 4 test functions in a single class.
2. Use `threading.Thread` + `Thread.join()` for synchronization.
3. Use `threading.Barrier` to maximize contention (all threads start simultaneously).
4. Run ruff → mypy → pytest.

### Method

`threading.Barrier(N)` makes all N threads wait until all have reached the barrier before proceeding, maximizing concurrent access.

### Details

**Test structure:**
```python
"""tests/test_semantic_cache_concurrency.py
Thread-safety regression tests for SemanticCache._lock (threading.RLock).
"""
from __future__ import annotations

import threading

from rag.cache import SemanticCache


_DIM = 4
_THREADS = 50


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

        threads = (
            [threading.Thread(target=_put, args=(i,)) for i in range(_THREADS)]
            + [threading.Thread(target=_lookup) for _ in range(_THREADS)]
        )
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
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| Lint | `uv run ruff check tests/test_semantic_cache_concurrency.py` | 0 errors |
| Type check | `uv run mypy tests/test_semantic_cache_concurrency.py` | no new errors |
| Tests | `uv run pytest tests/test_semantic_cache_concurrency.py -v` | 4 passed |
| Full suite | `uv run pytest tests/ -x -q` | no regressions |
