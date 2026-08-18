"""tests/shared/test_tool_executor_stampede.py
Tests for ToolExecutor._execute_with_stampede_protection() concurrent behavior.
"""

from __future__ import annotations

import asyncio
from typing import Any

import httpx
import pytest
from shared.tool_executor import ToolExecutor
from shared.transport_dto import ToolCallResult


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
            return ToolCallResult(
                output="ok", is_error=False, request_id="", server_key=""
            )

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
            return ToolCallResult(
                output="ok", is_error=False, request_id="", server_key=""
            )

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
                output="err",
                is_error=True,
                request_id="",
                server_key="",
                error_type="tool",
            )

        ex._raw_execute = _err  # type: ignore[method-assign]  -- test stub
        result = await ex._execute_with_stampede_protection("k", "t", {})
        assert result.is_error is True
        assert "k" not in ex._inflight
