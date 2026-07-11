# Implementation: tests/test_rag_cache.py (new file) — SemanticCache behavior tests

## Goal

Create the missing `tests/test_rag_cache.py` covering the 7 `SemanticCache` behaviors
named in the requirement's Tasks: zero-capacity handling, negative-capacity defensive
clamping, normal FIFO pruning, invalidate/generation bump, history-context separation,
embedding-dimension-mismatch errors, and lock re-entrancy safety for `size`/`generation`.

## Scope

**In:**
- New file `tests/test_rag_cache.py` with one test class and the 7 tests listed below.

**Out:**
- No changes to `scripts/rag/cache.py` itself (covered by a separate implementation doc;
  this doc assumes that fix is already applied when these tests run)
- No changes to `tests/test_semantic_cache_eviction.py` or
  `tests/test_semantic_cache_concurrency.py` (pre-existing, separate files; not touched)

## Assumptions

1. `SemanticCache` is importable as `from rag.cache import SemanticCache`.
2. Constructor signature: `SemanticCache(max_size: int = 100, threshold: float = 0.92)`.
3. `put(embedding: list[float], history_context: str, context_str: str) -> None` and
   `lookup(embedding: list[float], history_context: str = "") -> str | None` are the
   current method signatures (confirmed by direct read of `scripts/rag/cache.py`).
4. `prune()`'s `-0`/negative fix (companion doc
   `20260711-170448_rag_cache_prune_zero_negative_fix.md`) is implemented before or
   alongside this test file, since several tests assert its corrected behavior.
5. Constructing `SemanticCache(max_size=-5)` directly is a valid way to simulate a caller
   that bypasses `RagConfigValidator`'s negative-value rejection — the class itself has no
   constructor-level guard, only `prune()`'s defensive clamp.
6. `self._lock` is a `threading.RLock`, so calling a mutating method and then reading
   `size`/`generation` from the same thread/call stack must not deadlock once those
   properties acquire the lock too.

## Implementation

### Target file

`tests/test_rag_cache.py` (new)

### Procedure

1. Create the file with standard imports: `pytest` (if needed for fixtures — plain
   `assert`-based functions are sufficient here, no fixtures required) and
   `from rag.cache import SemanticCache`.
2. Define one test class, e.g. `TestSemanticCache`, or plain module-level test functions —
   follow the existing convention in `tests/test_semantic_cache_eviction.py` /
   `tests/test_semantic_cache_concurrency.py` for consistency (check which style those use
   and match it).
3. Implement the 7 tests (see Method for behavior of each).
4. Use small, fixed-dimension embeddings (e.g. dim=1 or dim=3) and `threshold=0.0` where
   the test only cares about pruning/invalidation mechanics, not similarity math (matches
   the precedent already used in `test_semantic_cache_eviction.py`).

### Method

Test-by-test behavior:

1. **`test_max_size_zero_keeps_no_entries`**: construct `SemanticCache(max_size=0)`; call
   `put()` several times with distinct embeddings/contexts; assert `cache.size == 0` after
   each `put()` call (not just after the last one).
2. **`test_negative_max_size_does_not_grow_unbounded`**: construct
   `SemanticCache(max_size=-5)` directly (bypassing validator); `put()` several entries;
   assert `cache.size == 0` after each — confirms `prune()`'s defensive clamp handles
   negative values the same as zero, not Python's negative-index slicing behavior.
3. **`test_fifo_pruning_normal`**: construct `SemanticCache(max_size=2)`; `put()` 3 entries
   with distinct embeddings and distinct `context_str` values (e.g. `"a"`, `"b"`, `"c"`);
   assert only the last 2 `context_str` values remain reachable (e.g. via `lookup()` with
   `threshold=0.0` and each entry's own embedding, or by inspecting `cache.size == 2` plus
   confirming the oldest (`"a"`) is no longer returned by `lookup()`).
4. **`test_invalidate_clears_entries_and_bumps_generation`**: `put()` one or more entries;
   record `cache.generation`; call `cache.invalidate()`; assert `cache.size == 0` and
   `cache.generation == <recorded> + 1`.
5. **`test_history_context_separation`**: `put()` two entries with the *same* embedding but
   different `history_context` values (e.g. `"session-a"`, `"session-b"`) and different
   `context_str` values; assert `lookup(embedding, history_context="session-a")` returns
   only the first entry's `context_str`, and `lookup(embedding, history_context="session-b")`
   returns only the second's.
6. **`test_embedding_dimension_mismatch_raises`**: `put()` a 3-dimensional embedding first
   (establishes `self._dim = 3`); then assert `pytest.raises(ValueError)` when calling
   either `put()` or `lookup()` with a 4-dimensional embedding.
7. **`test_size_and_generation_readable_without_lock_deadlock`**: call a mutating method
   (e.g. `put()` or `invalidate()`), then immediately read `cache.size` and
   `cache.generation` in the same test body/thread; assert both return without hanging and
   produce the expected values — a regression guard for the `RLock` re-entrancy fix (if
   `self._lock` were ever changed to a plain `threading.Lock`, this test would hang/deadlock,
   flagging the regression).

### Details

- Keep all 7 tests independent (no shared mutable fixture state across tests) — construct a
  fresh `SemanticCache` instance per test.
- Use plain `assert` statements; use `pytest.raises(ValueError)` for test 6.
- No mocking needed — `SemanticCache` has no external I/O dependencies.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check tests/test_rag_cache.py` | 0 errors |
| Type check | `uv run mypy scripts/rag/cache.py` (test file covered by pre-commit's mypy run per `rules/coding.md`) | No new errors |
| Tests | `uv run pytest tests/test_rag_cache.py -v` | All 7 tests pass |
| Regression | `uv run pytest tests/test_semantic_cache_eviction.py tests/test_semantic_cache_concurrency.py -v` | Pre-existing cache test files still pass unmodified |
