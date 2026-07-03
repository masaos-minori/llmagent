# Implementation: Create `tests/shared/test_tool_result_cache.py`

## Goal

Create a new test file `tests/shared/test_tool_result_cache.py` with 8 unit tests for
`ToolResultCache`, covering cache key format, miss, hit, TTL expiry, LRU ordering,
max-size eviction, error-result filtering, and clear.

## Scope

- In-Scope: New file `tests/shared/test_tool_result_cache.py` with `TestToolResultCache` class
  (8 test methods).
- Out-of-Scope: No changes to `tool_cache.py` or any other file.

## Assumptions

1. `scripts/shared/tool_cache.py` already contains `ToolResultCache` (prerequisite). Verify with
   `grep -n "class ToolResultCache" scripts/shared/tool_cache.py` before implementing.
2. `tests/shared/__init__.py` already exists (see `implementations/20260704-073815_tests_shared_init_py.md`).
3. `ToolCallResult` is importable from `shared.transport_dto`.
4. `time.sleep` can be used for TTL expiry tests with short durations (0.01s).
5. `uv run pytest` is the test runner; `asyncio_mode = "auto"` in `pyproject.toml`.

## Implementation

### Target file

`tests/shared/test_tool_result_cache.py` (new file)

### Procedure

1. Verify `ToolResultCache` exists: `grep -n "class ToolResultCache" scripts/shared/tool_cache.py`.
2. Create `tests/shared/test_tool_result_cache.py` with the content below.
3. Run `uv run ruff format tests/shared/test_tool_result_cache.py`.
4. Run `uv run ruff check tests/shared/test_tool_result_cache.py` — expect 0 errors.
5. Run `uv run pytest tests/shared/test_tool_result_cache.py -v` — expect 8 passed.

### Method

```python
"""tests/shared/test_tool_result_cache.py
Unit tests for ToolResultCache: key format, hit/miss, TTL, LRU, max_size, error filtering.
"""

from __future__ import annotations

import time

import pytest
from shared.tool_cache import ToolResultCache
from shared.transport_dto import ToolCallResult


def _ok_result(output: str = "ok") -> ToolCallResult:
    return ToolCallResult(output=output, is_error=False, request_id="", server_key="")


def _err_result() -> ToolCallResult:
    return ToolCallResult(
        output="err", is_error=True, request_id="", server_key="", error_type="tool"
    )


class TestToolResultCache:
    def test_make_key_format(self) -> None:
        cache = ToolResultCache(ttl=60.0)
        key = cache.make_key("read_file", {"path": "a"})
        assert key.startswith("read_file:")
        assert "path" in key

    def test_cache_miss_returns_none(self) -> None:
        cache = ToolResultCache(ttl=60.0)
        assert cache.get_result("nonexistent") is None

    def test_cache_hit_returns_result(self) -> None:
        cache = ToolResultCache(ttl=60.0)
        key = cache.make_key("my_tool", {})
        result = _ok_result("cached_output")
        cache.store_if_success(key, result)
        hit = cache.get_result(key)
        assert hit is not None
        assert hit.output == "cached_output"
        assert hit.is_error is False
        assert hit.request_id == ""

    def test_ttl_expiry_returns_none(self) -> None:
        cache = ToolResultCache(ttl=0.001)
        key = cache.make_key("my_tool", {})
        cache.store_if_success(key, _ok_result())
        time.sleep(0.02)
        assert cache.get_result(key) is None

    def test_lru_move_on_hit(self) -> None:
        cache = ToolResultCache(ttl=60.0, max_size=2)
        key_a = cache.make_key("tool_a", {})
        key_b = cache.make_key("tool_b", {})
        cache.store_if_success(key_a, _ok_result("a"))
        cache.store_if_success(key_b, _ok_result("b"))
        # Hit key_a — should move it to most-recently-used
        cache.get_result(key_a)
        # Add key_c — should evict key_b (LRU) not key_a
        key_c = cache.make_key("tool_c", {})
        cache.store_if_success(key_c, _ok_result("c"))
        assert cache.get_result(key_a) is not None
        assert cache.get_result(key_b) is None
        assert cache.get_result(key_c) is not None

    def test_max_size_eviction(self) -> None:
        cache = ToolResultCache(ttl=60.0, max_size=2)
        key_a = cache.make_key("tool_a", {})
        key_b = cache.make_key("tool_b", {})
        key_c = cache.make_key("tool_c", {})
        cache.store_if_success(key_a, _ok_result("a"))
        cache.store_if_success(key_b, _ok_result("b"))
        cache.store_if_success(key_c, _ok_result("c"))
        # key_a was first inserted → evicted as LRU
        assert cache.get_result(key_a) is None
        assert cache.get_result(key_b) is not None
        assert cache.get_result(key_c) is not None

    def test_error_result_not_stored(self) -> None:
        cache = ToolResultCache(ttl=60.0)
        key = cache.make_key("failing_tool", {})
        cache.store_if_success(key, _err_result())
        assert cache.get_result(key) is None

    def test_clear_empties_cache(self) -> None:
        cache = ToolResultCache(ttl=60.0)
        key = cache.make_key("my_tool", {})
        cache.store_if_success(key, _ok_result())
        cache.clear()
        assert cache.get_result(key) is None
```

### Details

- `_ok_result` and `_err_result` are module-level helpers to avoid repetition.
- `test_ttl_expiry_returns_none` uses `time.sleep(0.02)` which is a deliberate short
  sleep — acceptable in unit tests where sub-millisecond precision is not required.
- `test_lru_move_on_hit` verifies that accessing `key_a` promotes it to MRU before inserting
  `key_c`, so `key_b` (now LRU) is evicted. This tests the `move_to_end` call in `get_result()`.
- `ToolCallResult` default for `error_type` is `""` (confirmed at `transport_dto.py`).

## Validation plan

```bash
# Confirm prerequisite
grep -n "class ToolResultCache" scripts/shared/tool_cache.py

# Lint
uv run ruff check tests/shared/test_tool_result_cache.py
# Expected: 0 errors

# Run 8 tests
uv run pytest tests/shared/test_tool_result_cache.py -v
# Expected: 8 passed

# Regression
uv run pytest tests/test_tool_executor.py -q
# Expected: all pass
```
