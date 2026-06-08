"""tests/test_mcp_dispatch.py
Unit tests for mcp/dispatch.py — dispatch_tool.
"""

from __future__ import annotations

import pytest
from mcp.dispatch import _handle_tool_exception, dispatch_tool


class TestHandleToolException:
    def test_http_exception_returns_error_message(self) -> None:
        """HTTPException-like error returns formatted message."""

        class FakeHTTPException(Exception):
            status_code = 404
            detail = "Not found"

        exc = FakeHTTPException()
        msg, is_error = _handle_tool_exception("test_tool", exc)
        assert is_error
        assert "HTTP error (404): Not found" in msg

    def test_generic_exception_returns_error_message(self) -> None:
        """Generic exception returns error message."""
        exc = ValueError("something went wrong")
        msg, is_error = _handle_tool_exception("test_tool", exc)
        assert is_error
        assert "Tool error:" in msg


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
    async def test_handler_exception_returns_error(self) -> None:
        """Handler exception returns error."""

        async def handler(args: dict) -> str:
            raise ValueError("boom")

        result, is_error = await dispatch_tool({"boom": handler}, "boom", {})
        assert is_error
        assert "Tool error:" in result

    @pytest.mark.asyncio
    async def test_handler_http_exception_returns_error(self) -> None:
        """Handler HTTPException returns formatted error."""

        class FakeHTTPException(Exception):
            status_code = 403
            detail = "Forbidden"

        async def handler(args: dict) -> str:
            raise FakeHTTPException()

        result, is_error = await dispatch_tool({"boom": handler}, "boom", {})
        assert is_error
        assert "HTTP error (403): Forbidden" in result


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
