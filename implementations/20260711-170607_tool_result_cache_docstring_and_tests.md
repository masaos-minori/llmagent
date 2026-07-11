# Implementation: `ToolResultCache` clarifying docstring + `tests/test_tool_cache.py`

Source plan: `plans/20260711-170140_plan.md` (Phase 3).

## Goal

Clarify, in code, that `scripts/shared/tool_cache.py::ToolResultCache` is a standalone,
currently-unused utility — not the canonical cache `ToolExecutor` actually uses (`ToolExecutor`
maintains its own internal `OrderedDict`-based cache tightly integrated with stampede
protection). Add basic correctness tests for `ToolResultCache` since it remains public rather
than being removed.

## Scope

**In-Scope:**
- `scripts/shared/tool_cache.py`: replace/expand the current module docstring with one that
  explicitly states `ToolResultCache`'s unused/non-canonical status and points to
  `ToolExecutor`'s own `_execute_with_cache()` / `_store_and_evict()` as the actual cache path.
- `tests/test_tool_cache.py` (new file): basic correctness tests for `ToolResultCache` —
  get/store, TTL expiry, LRU eviction, error-result exclusion, clear, and key determinism.

**Out-of-Scope:**
- No migration of `ToolExecutor` to use `ToolResultCache` (explicitly conditional/out-of-scope
  per the source plan's Assumption 4 — the internal cache stays canonical).
- No changes to `scripts/shared/tool_executor.py` in this phase (that file's Phase 1 change is
  covered by a separate implementation doc).
- No removal or deprecation of `ToolResultCache` or `CacheEntry` — both stay public.

## Assumptions

1. `scripts/shared/tool_cache.py` (confirmed by direct read) already has a short module
   docstring (`"""shared/tool_cache.py\nCache entry dataclass and ToolResultCache for
   ToolExecutor's LRU result cache.\n"""`) that is misleading: it reads as if
   `ToolResultCache` IS used by `ToolExecutor`, when in fact `grep -rn "ToolResultCache"
   scripts/` confirms it is imported/instantiated nowhere in production code — only the
   `CacheEntry` dataclass is shared/reused conceptually (via a differently-named
   `_CacheEntry`/`CacheEntry` in `tool_executor.py`'s own internal cache, per prior
   implementation doc `implementations/done/20260615-110633_tool_cache.py.md`). This docstring
   must be corrected, not merely extended.
2. `ToolResultCache` (lines 26-54 of `scripts/shared/tool_cache.py`, confirmed by direct read)
   exposes: `__init__(self, ttl: float, max_size: int = 0)`, `make_key(tool_name, args) -> str`,
   `get_result(key) -> ToolCallResult | None`, `store_if_success(key, result) -> None`,
   `clear() -> None`.
2a. `get_result()` deletes an expired entry and returns `None` when `age >= self._ttl`;
   `store_if_success()` is a no-op when `result.is_error` is `True`; `store_if_success()` evicts
   the least-recently-used entry via `OrderedDict.popitem(last=False)` once `len(self._cache) >
   self._max_size` (only when `max_size > 0`); `make_key()` returns
   `f"{tool_name}:{_json_dumps(args)}"` — deterministic for identical `(tool_name, args)` pairs
   because `shared.json_utils.dumps` (aliased `_json_dumps`) must serialize consistently for
   equal input (verify key-sorting behavior when writing the determinism test, e.g. by using an
   `args` dict with multiple keys and confirming two calls with the same dict produce the same
   key string).
3. `tests/test_tool_cache.py` does not exist (confirmed by `find`) — this is a new file, not an
   extension of an existing one.
4. `ToolCallResult` is importable from `shared.transport_dto` (already used inside
   `tool_cache.py` itself) — tests can construct/inspect it directly without further imports
   from `tool_executor.py`.

## Implementation

### Target file

`scripts/shared/tool_cache.py` (docstring-only change), `tests/test_tool_cache.py` (new file)

### Procedure

1. In `scripts/shared/tool_cache.py`, replace the current module docstring (lines 2-4) with the
   clarified version in Method below. No other lines in this file change.
2. Create `tests/test_tool_cache.py` with a `TestToolResultCache` class containing the 6 test
   methods listed in Method below.
3. Run lint, type check, and the targeted test file per Validation plan below.

### Method

**Docstring replacement** (`scripts/shared/tool_cache.py`, top of file):

```python
#!/usr/bin/env python3
"""shared/tool_cache.py
Cache entry dataclass and ToolResultCache for a standalone tool-result cache.

Status: ToolResultCache is NOT currently used by ToolExecutor -- ToolExecutor
maintains its own internal OrderedDict-based cache (see _execute_with_cache(),
_store_and_evict() in shared/tool_executor.py), tightly integrated with its
stampede-protection (_inflight future sharing) mechanism, which this class has
no equivalent of. ToolResultCache remains available as a standalone, simpler
utility for a future caller that needs LRU+TTL caching without stampede
protection -- it is not deprecated, but it is also not the canonical cache.
"""
```

**New file** (`tests/test_tool_cache.py`), method signatures only:

```python
"""tests/test_tool_cache.py
Correctness tests for shared.tool_cache.ToolResultCache.
"""

from __future__ import annotations

from shared.tool_cache import ToolResultCache
from shared.transport_dto import ToolCallResult


class TestToolResultCache:
    def test_store_and_get_result(self) -> None:
        """A stored successful result is retrievable via get_result() before TTL expiry."""
        ...

    def test_ttl_expiry_returns_none(self) -> None:
        """get_result() returns None (and evicts) once the entry's age exceeds ttl."""
        ...

    def test_lru_eviction_at_max_size(self) -> None:
        """Storing beyond max_size evicts the least-recently-used entry, not the newest."""
        ...

    def test_store_if_success_skips_error_results(self) -> None:
        """store_if_success() is a no-op when result.is_error is True."""
        ...

    def test_clear_removes_all_entries(self) -> None:
        """clear() empties the cache; get_result() returns None for a previously-stored key."""
        ...

    def test_make_key_is_deterministic_for_same_args(self) -> None:
        """make_key() returns an identical string for two calls with equal tool_name/args."""
        ...
```

### Details

- `test_ttl_expiry_returns_none`: construct `ToolResultCache(ttl=<small value>)`, store a
  result, advance time past the TTL (e.g. via `time.sleep()` with a very small `ttl` like
  `0.01`, or by monkeypatching `time.time` if a deterministic/faster test is preferred — prefer
  monkeypatching to avoid a slow/flaky sleep-based test), then assert `get_result()` returns
  `None` and the key is removed from the internal `_cache` (may need to access the private
  `_cache` attribute directly for the eviction assertion, acceptable in a same-module test
  file).
- `test_lru_eviction_at_max_size`: construct `ToolResultCache(ttl=<large value>, max_size=2)`,
  store 3 distinct keys in order, assert the first (least-recently-used, never re-accessed)
  key is evicted (`get_result()` returns `None` for it) while the other two remain retrievable.
- `test_store_if_success_skips_error_results`: construct a `ToolCallResult` with
  `is_error=True`, call `store_if_success()`, then assert `get_result()` returns `None` for that
  key (never stored).
- `test_make_key_is_deterministic_for_same_args`: call `make_key()` twice with the same
  `tool_name` and an equal (but freshly-constructed, not the same object) `args` dict; assert
  the two returned strings are equal.
- Use `ToolCallResult(output=..., is_error=..., request_id="", server_key="")` (minimal required
  fields) when constructing test fixtures — confirm the exact required/optional fields by
  reading `shared/transport_dto.py::ToolCallResult` before writing the tests, matching the
  construction style already used in `tests/test_tool_executor.py`.

## Validation plan

Filtered to checks relevant to this file, per the plan's Validation plan table:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/shared/tool_cache.py tests/test_tool_cache.py` | 0 errors |
| Type check | `uv run mypy scripts/shared/tool_cache.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations (no import changes) |
| Tests | `uv run pytest tests/test_tool_cache.py -v` | All 6 new tests pass |
| Docs | `uv run python tools/check_docs_consistency.py` | Passes |
