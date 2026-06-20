# Implementation: test_semantic_cache_eviction.py

## Goal
Create `tests/test_semantic_cache_eviction.py` to verify that `SemanticCache`
evicts entries in FIFO order (oldest inserted is evicted first when over capacity).

## Scope
- New file: `tests/test_semantic_cache_eviction.py`
- Tests for: FIFO eviction order, overflow behavior, lookup after eviction,
  empty-string vs None normalized_content edge cases (not applicable here —
  that is for FTS; skip those for SemanticCache)

## Assumptions
- `SemanticCache` is importable from `rag.cache`
- Embeddings are simple fixed-dimension float lists; tests use dim=3 for simplicity
- `lookup()` uses cosine similarity; for identical embeddings, similarity = 1.0
- `threshold=0.0` allows any similarity to hit — simplifies testing eviction without
  worrying about cosine math
- FIFO: entry inserted first is evicted first when `put()` exceeds `max_size`

## Implementation

### Target file
`tests/test_semantic_cache_eviction.py`

### Procedure
Write a pytest test file with 4 test cases covering eviction behavior.

### Method
New test file with `pytest` style functions.

### Details

```python
"""tests/test_semantic_cache_eviction.py
Verifies that SemanticCache uses FIFO eviction (oldest entry removed first).
"""
from __future__ import annotations

import pytest
from rag.cache import SemanticCache


def _emb(x: float) -> list[float]:
    """Return a unit-like 3-dim embedding for testing."""
    return [x, 0.0, 0.0]


class TestSemanticCacheFifoEviction:
    def test_oldest_entry_evicted_on_overflow(self) -> None:
        """Put max_size+1 entries; the first entry should be evicted."""
        cache = SemanticCache(max_size=2, threshold=0.0)
        cache.put(_emb(1.0), "", "result_A")
        cache.put(_emb(2.0), "", "result_B")
        # Third entry overflows max_size=2; oldest (emb 1.0 → "result_A") is evicted
        cache.put(_emb(3.0), "", "result_C")
        # "result_A" should be gone
        assert cache.lookup(_emb(1.0)) is None
        # "result_B" and "result_C" should still be present
        assert cache.lookup(_emb(2.0)) is not None
        assert cache.lookup(_emb(3.0)) is not None

    def test_newest_entry_not_evicted(self) -> None:
        """The most recently inserted entry is never evicted on immediate overflow."""
        cache = SemanticCache(max_size=1, threshold=0.0)
        cache.put(_emb(1.0), "", "result_A")
        cache.put(_emb(2.0), "", "result_B")  # evicts A
        assert cache.lookup(_emb(2.0)) is not None
        assert cache.lookup(_emb(1.0)) is None

    def test_no_eviction_within_capacity(self) -> None:
        """Entries within max_size are not evicted."""
        cache = SemanticCache(max_size=3, threshold=0.0)
        cache.put(_emb(1.0), "", "r1")
        cache.put(_emb(2.0), "", "r2")
        cache.put(_emb(3.0), "", "r3")
        assert cache.lookup(_emb(1.0)) is not None
        assert cache.lookup(_emb(2.0)) is not None
        assert cache.lookup(_emb(3.0)) is not None

    def test_size_stays_at_max_after_multiple_puts(self) -> None:
        """Cache size never exceeds max_size after repeated puts."""
        cache = SemanticCache(max_size=2, threshold=0.0)
        for i in range(10):
            cache.put([float(i), 0.0, 0.0], "", f"result_{i}")
        assert cache.size == 2
```

## Validation plan

| Check | Command | Expected |
|---|---|---|
| All 4 tests pass | `uv run pytest tests/test_semantic_cache_eviction.py -v` | 4 passed |
| Lint | `uv run ruff check tests/test_semantic_cache_eviction.py` | 0 errors |
| Type check | `uv run mypy tests/test_semantic_cache_eviction.py` | no errors |
| Full suite | `uv run pytest -q` | no new failures |
