"""tests/test_mcp_dispatch.py
Unit tests for mcp/dispatch.py — dispatch_tool.
"""

from __future__ import annotations

import pytest
from mcp.dispatch import dispatch_tool


class TestDispatchTool:
    @pytest.mark.asyncio
    async def test_dispatches_to_handler(self) -> None:
        """Dispatch calls the correct handler."""

        async def handler(args: dict) -> str:
            return f"result:{args.get('x')}"

        result, is_error = await dispatch_tool(
            {"my_tool": handler}, "my_tool", {"x": 123}
        )
        assert not is_error
        assert result == "result:123"

    @pytest.mark.asyncio
    async def test_empty_tool_name_returns_error(self) -> None:
        """Empty tool name returns error."""
        result, is_error = await dispatch_tool({}, "", {})
        assert is_error
        assert "non-empty" in result

    @pytest.mark.asyncio
    async def test_non_string_tool_name_returns_error(self) -> None:
        """Non-string tool name returns error."""
        result, is_error = await dispatch_tool({}, 123, {})  # type: ignore[arg-type]
        assert is_error
        assert "non-empty" in result

    @pytest.mark.asyncio
    async def test_whitespace_tool_name_returns_error(self) -> None:
        """Whitespace-only tool name returns error."""
        result, is_error = await dispatch_tool({}, "   ", {})
        assert is_error
        assert "non-empty" in result

    @pytest.mark.asyncio
    async def test_unknown_tool_returns_error(self) -> None:
        """Unknown tool returns error."""
        result, is_error = await dispatch_tool({"known": lambda a: ""}, "unknown", {})
        assert is_error
        assert "Unknown tool" in result

    @pytest.mark.asyncio
    async def test_value_error_from_handler_returns_validation_error(self) -> None:
        """ValueError from handler returns validation error result."""

        async def handler(args: dict) -> str:
            raise ValueError("bad input")

        result, is_error = await dispatch_tool({"tool": handler}, "tool", {})
        assert is_error
        assert "Validation error" in result

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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
