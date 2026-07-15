# Implementation Procedure: tests/shared/test_tool_result_cache.py

Source plan: `plans/20260715-140914_plan.md`

## Prior-doc status

No existing implementation document targets this file under any prior plan
(searched `implementations/` and `implementations/done/` for
`test_tool_result_cache`; no match). This document is written fresh.

## Goal

Add a regression test proving `server_key` round-trips through
`ToolResultCache.store_if_success()` / `get_result()` and that a cache hit
carries `source="cache"`, once
`implementations/20260715-152212_tool_cache.py.md` is applied.

## Scope

**In scope**
- Add `test_cache_hit_preserves_server_key` — store a result with a non-empty
  `server_key`, retrieve it, assert the retrieved `ToolCallResult.server_key`
  matches and `source == "cache"`.
- Update `_ok_result()` helper (or add a variant) to accept/pass a
  `server_key` so the new test can construct a result with a realistic,
  non-empty value.

**Out of scope**
- No change to `test_make_key_format`, `test_cache_miss_returns_none`,
  `test_ttl_expiry_returns_none`, `test_lru_move_on_hit`,
  `test_max_size_eviction`, `test_error_result_not_stored`,
  `test_clear_empties_cache` — all pass unmodified (none assert on
  `server_key` or `source` today).
- `test_cache_hit_returns_result` (current lines 34-43) does not currently
  assert on `source`; leaving it unmodified is acceptable since the new test
  covers the `source="cache"` assertion explicitly, but if reviewers prefer,
  a `assert hit.source == "cache"` line may be added there too — not required
  for this plan's acceptance criteria.

## Assumptions

- Depends on `implementations/20260715-152212_tool_cache.py.md` being applied
  first (`CacheEntry.server_key` field, `store_if_success`/`get_result`
  propagation).
- Current `_ok_result()` helper (lines 13-14) does not accept a `server_key`
  parameter; extending it with a keyword-only default (`server_key: str =
  ""`) keeps all seven existing call sites (which pass no `server_key`)
  unaffected.

## Implementation

### Target file

`tests/shared/test_tool_result_cache.py`

### Procedure

1. Update `_ok_result()` (lines 13-14) to accept an optional `server_key: str
   = ""` parameter and pass it through to `ToolCallResult(...)`.
2. Add `test_cache_hit_preserves_server_key` to `TestToolResultCache`, placed
   after `test_cache_hit_returns_result` (ends line 43).

### Method

Additive test-only edit; extend one helper's signature with a
backward-compatible default, add one new test method.

### Details

```python
def _ok_result(output: str = "ok", server_key: str = "") -> ToolCallResult:
    return ToolCallResult(
        output=output, is_error=False, request_id="", server_key=server_key
    )
```

```python
    def test_cache_hit_preserves_server_key(self) -> None:
        cache = ToolResultCache(ttl=60.0)
        key = cache.make_key("rag_run_pipeline", {})
        result = _ok_result("cached_output", server_key="rag_pipeline")
        cache.store_if_success(key, result)
        hit = cache.get_result(key)
        assert hit is not None
        assert hit.server_key == "rag_pipeline"
        assert hit.source == "cache"
```

## Validation plan

| Check | Command | Expected outcome |
|---|---|---|
| Depends on | `implementations/20260715-152212_tool_cache.py.md` applied first | `CacheEntry.server_key` exists; `get_result`/`store_if_success` propagate it |
| Format/lint | `uv run ruff format tests/shared/test_tool_result_cache.py && uv run ruff check tests/shared/test_tool_result_cache.py` | 0 errors |
| Type check | `uv run mypy tests/shared/test_tool_result_cache.py` | 0 new errors |
| Targeted tests | `uv run pytest tests/shared/test_tool_result_cache.py -v` | All existing + new test pass |
| Full suite | `uv run pytest -v` | No new failures |
