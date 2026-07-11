# Implementation: scripts/rag/cache.py — fix prune() -0/negative bug, lock size/generation

## Goal

Fix `SemanticCache.prune()` so that `max_size <= 0` produces a well-defined "capacity
zero" cache (holds no entries) instead of the current bug where `max_size=0` causes
`self._entries[-0:]` to evaluate as `self._entries[0:]` (the entire list — Python
`-0 == 0`), letting the cache grow unbounded. Also move the `size` and `generation`
property reads under the existing `self._lock` to close a narrow thread-safety gap.

## Scope

**In:**
- `scripts/rag/cache.py::SemanticCache.prune()` — correct handling for `max_size <= 0`
  (including negative values, defensively)
- `scripts/rag/cache.py::SemanticCache.size` (property) — read under `self._lock`
- `scripts/rag/cache.py::SemanticCache.generation` (property) — read under `self._lock`

**Out:**
- No change to `lookup()`, `put()`, `invalidate()` — already lock-protected
- No change to `CacheEntry` / `rag/models_data.py`
- No change to the validator (`scripts/shared/config_validator.py`) — covered by a
  separate implementation doc
- No change to `RagPipeline`'s own `RagConfig`-typed `cfg` construction

## Assumptions

1. `prune()` (current lines 92-96) does `self._entries[-self._max_size:]` — confirmed by
   direct read. When `max_size=0`, `-self._max_size == 0`, so `self._entries[0:]` returns
   the full list unchanged: the bug.
2. Design decision (plan Assumption 2): `max_size <= 0` means "capacity zero" — the cache
   holds zero entries. This is not "disabled" in the `use_semantic_cache` sense (that is a
   separate, existing boolean flag on `RagPipelineConfig`); it is a defense-in-depth,
   independent guarantee of zero cache growth via capacity.
3. Negative `max_size` has no sensible interpretation (Python negative-index slicing would
   keep everything-except-the-first-N, again growing unbounded) — clamp defensively in
   `prune()` itself (`max(self._max_size, 0)` semantics), in addition to `RagConfigValidator`
   rejecting negative values at the config boundary (separate doc). Both layers guard
   independently per this codebase's established pattern.
4. `size` and `generation` properties (current lines 98-100, 108-110) currently read
   `self._entries` / `self._generation` without acquiring `self._lock`, while every
   mutating method already does. `self._lock` is a `threading.RLock` (re-entrant), so
   acquiring it inside a property that might be read from within another locked method's
   call stack is safe and will not deadlock.

## Implementation

### Target file

`scripts/rag/cache.py`

### Procedure

1. In `prune()`, replace the current `if len(self._entries) > self._max_size:` /
   `self._entries = self._entries[-self._max_size:]` body with an explicit branch:
   - If `self._max_size <= 0`: set `self._entries = []` (empty the cache unconditionally).
   - Elif `len(self._entries) > self._max_size`: keep the existing FIFO-tail slice
     `self._entries = self._entries[-self._max_size:]` (this branch is unreachable for
     `max_size <= 0` since it is now handled above, closing the `-0` bug at the source).
2. Keep `prune()`'s body inside the existing `with self._lock:` block (no change to lock
   usage there — it already acquires the lock).
3. Update `prune()`'s docstring to state the `max_size <= 0` semantics explicitly (see
   Design in the plan for exact wording), so the behavior is self-documenting at the
   source, not just in `docs/`.
4. Change the `size` property body from `return len(self._entries)` to acquire
   `self._lock` first: `with self._lock: return len(self._entries)`.
5. Change the `generation` property body from `return self._generation` to acquire
   `self._lock` first: `with self._lock: return self._generation`.
6. No signature changes to any public method — `prune()`, `size`, `generation` keep their
   existing call contracts.

### Method

Direct, minimal edit to `scripts/rag/cache.py`: rewrite `prune()`'s conditional body, and
wrap the two property bodies in `with self._lock:`. No new imports, no new fields.

### Details

- `prune()`'s only caller is `put()` (same class, already inside `with self._lock:` when
  it calls `self.prune()` — safe because `self._lock` is an `RLock`).
- Do not clamp `self._max_size` itself at `__init__` time — clamp only inside `prune()`'s
  logic, so `self._max_size` still reflects the raw configured value (useful for any
  future introspection/logging) while pruning behavior is always well-defined.
- Behavior is unchanged for every `max_size > 0` case (the only cases any existing test
  currently exercises) — this is a bug fix scoped strictly to the `max_size <= 0` edge
  case plus a lock-correctness fix for two read-only properties.

## Validation plan

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/rag/cache.py` | 0 errors |
| Type check | `uv run mypy scripts/rag/cache.py` | No new errors |
| Tests | `uv run pytest tests/test_rag_cache.py -v` | `test_max_size_zero_keeps_no_entries`, `test_negative_max_size_does_not_grow_unbounded`, `test_fifo_pruning_normal`, `test_size_and_generation_readable_without_lock_deadlock` all pass (see companion test-file implementation doc) |
| Manual | `PYTHONPATH=scripts uv run python -c "from rag.cache import SemanticCache; c = SemanticCache(max_size=0); c.put([1.0], '', 'x'); assert c.size == 0"` | Confirms the `-0` bug fix directly, independent of pytest |
| Regression | `uv run pytest tests/test_rag_pipeline.py tests/test_mcp_rag_pipeline.py tests/test_rag_pipeline_mcp_service.py -q` | No new failures |
