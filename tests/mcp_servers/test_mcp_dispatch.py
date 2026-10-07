"""tests/test_mcp_dispatch.py
Unit tests for mcp/dispatch.py — dispatch_tool.
"""

from __future__ import annotations

from collections.abc import Iterator
from typing import Any

import pytest
from mcp_servers.dispatch import (
    _IDEMPOTENCY_CACHE_MAX_ENTRIES,
    _IDEMPOTENCY_CACHE_TTL_SECONDS,
    _duplicate_cache,
    _is_side_effecting,
    dispatch_tool,
)


class TestDispatchTool:
    @pytest.mark.asyncio
    async def test_dispatches_to_handler(self) -> None:
        """Dispatch calls the correct handler."""

        async def handler(args: dict) -> str:
            return f"result:{args.get('x')}"

        res = await dispatch_tool({"my_tool": handler}, "my_tool", {"x": 123})
        assert not res.is_error
        assert res.output == "result:123"

    @pytest.mark.asyncio
    async def test_empty_tool_name_returns_error(self) -> None:
        """Empty tool name returns error."""
        res = await dispatch_tool({}, "", {})
        assert res.is_error
        assert "non-empty" in res.output

    @pytest.mark.asyncio
    async def test_non_string_tool_name_returns_error(self) -> None:
        """Non-string tool name returns error."""
        res = await dispatch_tool({}, 123, {})  # type: ignore[arg-type]
        assert res.is_error
        assert "non-empty" in res.output

    @pytest.mark.asyncio
    async def test_whitespace_tool_name_returns_error(self) -> None:
        """Whitespace-only tool name returns error."""
        res = await dispatch_tool({}, "   ", {})
        assert res.is_error
        assert "non-empty" in res.output

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self) -> None:
        """Unknown tool returns error."""
        res = await dispatch_tool({"known": lambda a: ""}, "unknown", {})
        assert res.is_error
        assert "Unknown tool" in res.output

    @pytest.mark.asyncio
    async def test_value_error_from_handler_returns_validation_error(self) -> None:
        """ValueError from handler returns validation error result."""

        async def handler(args: dict) -> str:
            raise ValueError("bad input")

        res = await dispatch_tool({"tool": handler}, "tool", {})
        assert res.is_error
        assert "Validation error" in res.output

    @pytest.mark.asyncio
    async def test_non_value_error_propagates(self) -> None:
        """Non-ValueError exceptions (runtime errors) propagate to the caller."""

        async def handler(args: dict) -> str:
            raise RuntimeError("internal failure")

        with pytest.raises(RuntimeError, match="internal failure"):
            await dispatch_tool({"tool": handler}, "tool", {})

    @pytest.mark.asyncio
    async def test_http_exception_propagates(self) -> None:
        """HTTP exceptions propagate to the caller (not swallowed)."""

        class FakeHTTPException(Exception):
            status_code = 403
            detail = "Forbidden"

        async def handler(args: dict) -> str:
            raise FakeHTTPException()

        with pytest.raises(FakeHTTPException):
            await dispatch_tool({"tool": handler}, "tool", {})


class TestDispatchIdempotencyCache:
    """Cache behavior of dispatch_tool() (REQ-001..REQ-004).

    Exercises the dedup path by dispatching a genuine side-effecting tool
    (``write_file``) with explicit ``idempotency_key`` values. Clears the
    module-level ``_duplicate_cache`` around each case to isolate them.
    """

    @pytest.fixture(autouse=True)
    def _clear_idem_cache(self) -> Iterator[None]:
        _duplicate_cache.clear()
        yield
        _duplicate_cache.clear()

    @staticmethod
    def _side_effecting_tool() -> str:
        name = "write_file"
        assert _is_side_effecting(name)
        return name

    @pytest.mark.asyncio
    async def test_keyless_and_empty_key_always_execute(self) -> None:
        """A keyless or empty-key call never touches the cache (REQ-001)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "wrote"

        tool = self._side_effecting_tool()
        for key in (None, ""):
            r1 = await dispatch_tool(
                {tool: handler}, tool, {"p": "a"}, idempotency_key=key
            )
            r2 = await dispatch_tool(
                {tool: handler}, tool, {"p": "a"}, idempotency_key=key
            )
            assert not r1.is_error and not r2.is_error
        assert len(calls) == 4  # executed every time across both keyless calls
        assert len(_duplicate_cache) == 0  # nothing stored

    @pytest.mark.asyncio
    async def test_same_key_served_from_cache(self) -> None:
        """Same key + same tool + same args: handler runs once, second is cached (REQ-002)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "wrote"

        tool = self._side_effecting_tool()
        key = "same-key"
        r1 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, idempotency_key=key)
        r2 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, idempotency_key=key)
        assert not r1.is_error and not r2.is_error
        assert r1.output == r2.output == "wrote"
        assert len(calls) == 1  # executed once
        assert len(_duplicate_cache) == 1

    @pytest.mark.asyncio
    async def test_same_key_different_tool_rejected(self) -> None:
        """Same key reused for a different tool is rejected without a second execution (REQ-002)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "wrote"

        table = {"write_file": handler, "shell_run": handler}
        r1 = await dispatch_tool(table, "write_file", {"p": "a"}, idempotency_key="k")
        r2 = await dispatch_tool(table, "shell_run", {"p": "a"}, idempotency_key="k")
        assert not r1.is_error
        assert r2.is_error
        assert "reused with different content" in r2.output
        assert len(calls) == 1  # second did not execute

    @pytest.mark.asyncio
    async def test_same_key_different_args_rejected(self) -> None:
        """Same key reused with different arguments is rejected without a second execution (REQ-002)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "wrote"

        tool = self._side_effecting_tool()
        r1 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, idempotency_key="k")
        r2 = await dispatch_tool({tool: handler}, tool, {"p": "b"}, idempotency_key="k")
        assert not r1.is_error
        assert r2.is_error
        assert "reused with different content" in r2.output
        assert len(calls) == 1

    @pytest.mark.asyncio
    async def test_ttl_expiry_reexecutes(self, monkeypatch: Any) -> None:
        """After the TTL elapses a repeat call re-executes instead of serving stale (REQ-003)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "wrote"

        clock: dict[str, float] = {"t": 1000.0}
        monkeypatch.setattr("mcp_servers.dispatch._idem_now", lambda: clock["t"])
        tool = self._side_effecting_tool()
        key = "ttl-key"
        await dispatch_tool({tool: handler}, tool, {"p": "a"}, idempotency_key=key)
        clock["t"] = 1000.0 + _IDEMPOTENCY_CACHE_TTL_SECONDS // 2  # within TTL
        await dispatch_tool({tool: handler}, tool, {"p": "a"}, idempotency_key=key)
        assert len(calls) == 1  # served from cache
        clock["t"] = 1000.0 + _IDEMPOTENCY_CACHE_TTL_SECONDS + 1.0  # past TTL
        r3 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, idempotency_key=key)
        assert not r3.is_error
        assert len(calls) == 2  # expired, re-executed

    @pytest.mark.asyncio
    async def test_eviction_reexecutes_oldest(self) -> None:
        """Exceeding the max entry count evicts the oldest; an evicted key re-executes (REQ-003)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return "wrote"

        tool = self._side_effecting_tool()
        table = {tool: handler}
        for i in range(_IDEMPOTENCY_CACHE_MAX_ENTRIES + 5):
            await dispatch_tool(table, tool, {"i": i}, idempotency_key=f"k{i}")
        # Oldest keys were evicted -> a repeat re-executes.
        before = len(calls)
        r0 = await dispatch_tool(table, tool, {"i": 0}, idempotency_key="k0")
        assert not r0.is_error
        assert len(calls) == before + 1
        # A still-present middle key is served from cache (no re-execution).
        mid_before = len(calls)
        await dispatch_tool(table, tool, {"i": 100}, idempotency_key="k100")
        assert len(calls) == mid_before

    @pytest.mark.asyncio
    async def test_error_result_not_cached(self) -> None:
        """A ValueError result is never cached; a repeat identical call re-executes (REQ-004)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            raise ValueError("bad input")

        tool = self._side_effecting_tool()
        r1 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, idempotency_key="k")
        assert r1.is_error
        assert "Validation error" in r1.output
        assert len(_duplicate_cache) == 0
        calls.clear()
        r2 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, idempotency_key="k")
        assert r2.is_error
        assert len(calls) == 1  # re-executed, not served

    @pytest.mark.asyncio
    async def test_dry_run_result_not_cached(self) -> None:
        """A dry-run result is never cached; a repeat call re-executes (REQ-004 / UNK-01)."""

        calls: list[int] = []

        async def handler(args: dict) -> str:
            calls.append(1)
            return '{"dry_run": true}'

        tool = self._side_effecting_tool()
        r1 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, idempotency_key="k")
        assert not r1.is_error
        assert len(_duplicate_cache) == 0
        calls.clear()
        r2 = await dispatch_tool({tool: handler}, tool, {"p": "a"}, idempotency_key="k")
        assert not r2.is_error
        assert len(calls) == 1  # re-executed, not served


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
