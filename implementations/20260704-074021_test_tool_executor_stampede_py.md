# Implementation: Create `tests/shared/test_tool_executor_stampede.py`

## Goal

Create a new test file `tests/shared/test_tool_executor_stampede.py` with 5 async tests for
`ToolExecutor._execute_with_stampede_protection()`, verifying that concurrent callers correctly
share results on success and propagate exceptions on failure, and that `_inflight` is cleaned up
in both cases.

## Scope

- In-Scope: New file `tests/shared/test_tool_executor_stampede.py` with `TestStampedeProtection`
  class (5 test methods).
- Out-of-Scope: No changes to production code. `tests/shared/__init__.py` must already exist.

## Assumptions

1. The fix to `_execute_with_stampede_protection()` (try/except/else/finally) is already applied
   to `scripts/shared/tool_executor.py` (prerequisite).
2. `tests/shared/__init__.py` already exists.
3. `ToolExecutor` can be constructed with `http=httpx.AsyncClient()` and empty `server_configs={}`.
4. `_raw_execute` can be replaced via direct attribute assignment for test isolation.
5. `uv run pytest` with `asyncio_mode = "auto"` supports `pytest.mark.asyncio` tests.

## Implementation

### Target file

`tests/shared/test_tool_executor_stampede.py` (new file)

### Procedure

1. Create `tests/shared/test_tool_executor_stampede.py` with the content below.
2. Run `uv run ruff format tests/shared/test_tool_executor_stampede.py`.
3. Run `uv run ruff check tests/shared/test_tool_executor_stampede.py` — expect 0 errors.
4. Run `uv run pytest tests/shared/test_tool_executor_stampede.py -v` — expect 5 passed.

### Method

```python
"""tests/shared/test_tool_executor_stampede.py
Tests for ToolExecutor._execute_with_stampede_protection() concurrent behavior.
"""

from __future__ import annotations

import asyncio
from typing import Any
from unittest.mock import AsyncMock

import httpx
import pytest
from shared.tool_executor import ToolCallResult, ToolExecutor


def _make_executor() -> ToolExecutor:
    return ToolExecutor(http=httpx.AsyncClient(), cache_ttl=60.0, server_configs={})


class TestStampedeProtection:
    @pytest.mark.asyncio
    async def test_concurrent_success_calls_raw_execute_once(self) -> None:
        ex = _make_executor()
        call_count = 0

        async def _fake(tool_name: str, args: dict[str, Any]) -> ToolCallResult:
            nonlocal call_count
            call_count += 1
            await asyncio.sleep(0.01)
            return ToolCallResult(output="ok", is_error=False, request_id="", server_key="")

        ex._raw_execute = _fake  # type: ignore[method-assign]  -- test stub
        results = await asyncio.gather(
            ex._execute_with_stampede_protection("k", "t", {}),
            ex._execute_with_stampede_protection("k", "t", {}),
        )
        assert call_count == 1
        assert all(r.output == "ok" for r in results)

    @pytest.mark.asyncio
    async def test_concurrent_exception_both_receive_exception(self) -> None:
        ex = _make_executor()

        async def _fail(tool_name: str, args: dict[str, Any]) -> ToolCallResult:
            await asyncio.sleep(0.01)
            raise RuntimeError("boom")

        ex._raw_execute = _fail  # type: ignore[method-assign]  -- test stub
        with pytest.raises(RuntimeError, match="boom"):
            await asyncio.gather(
                ex._execute_with_stampede_protection("k", "t", {}),
                ex._execute_with_stampede_protection("k", "t", {}),
            )

    @pytest.mark.asyncio
    async def test_inflight_cleaned_up_on_success(self) -> None:
        ex = _make_executor()

        async def _ok(tool_name: str, args: dict[str, Any]) -> ToolCallResult:
            return ToolCallResult(output="ok", is_error=False, request_id="", server_key="")

        ex._raw_execute = _ok  # type: ignore[method-assign]  -- test stub
        await ex._execute_with_stampede_protection("k", "t", {})
        assert "k" not in ex._inflight

    @pytest.mark.asyncio
    async def test_inflight_cleaned_up_on_exception(self) -> None:
        ex = _make_executor()

        async def _fail(tool_name: str, args: dict[str, Any]) -> ToolCallResult:
            raise RuntimeError("fail")

        ex._raw_execute = _fail  # type: ignore[method-assign]  -- test stub
        with pytest.raises(RuntimeError):
            await ex._execute_with_stampede_protection("k", "t", {})
        assert "k" not in ex._inflight

    @pytest.mark.asyncio
    async def test_error_tool_result_not_cached_by_stampede(self) -> None:
        ex = _make_executor()

        async def _err(tool_name: str, args: dict[str, Any]) -> ToolCallResult:
            return ToolCallResult(
                output="err", is_error=True, request_id="", server_key="", error_type="tool"
            )

        ex._raw_execute = _err  # type: ignore[method-assign]  -- test stub
        result = await ex._execute_with_stampede_protection("k", "t", {})
        assert result.is_error is True
        assert "k" not in ex._inflight
```

### Details

- `ex._raw_execute = _fake` uses direct attribute assignment to replace the method on the instance.
  `# type: ignore[method-assign]` is required because the type annotation expects the bound method.
- `test_concurrent_exception_both_receive_exception` uses `asyncio.gather` with `pytest.raises`.
  Note that `asyncio.gather` by default raises the first exception — the second coroutine's
  exception may be suppressed. If both coroutines receive the exception, one re-raises immediately
  from `await inflight` and the other re-raises from the `except` block. Use
  `asyncio.gather(..., return_exceptions=True)` if you need to inspect both results.
- `test_error_tool_result_not_cached_by_stampede` verifies that an `is_error=True` result does
  NOT get cached (caching logic is in `_execute_with_cache`, not in `_execute_with_stampede_protection`).
  This test verifies only that `_inflight` is cleaned up correctly on error results.

## Validation plan

```bash
# Lint
uv run ruff check tests/shared/test_tool_executor_stampede.py
# Expected: 0 errors

# Run 5 tests
uv run pytest tests/shared/test_tool_executor_stampede.py -v
# Expected: 5 passed

# Regression
uv run pytest tests/test_tool_executor.py -q
# Expected: all pass
```
