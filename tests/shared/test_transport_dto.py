"""tests/shared/test_transport_dto.py
Unit tests for ToolCallResult.from_transport error_type classification.
"""

from __future__ import annotations

from shared.transport_dto import ToolCallResult


class TestFromTransport:
    def test_server_reported_error_is_tool_error(self) -> None:
        # The server responded (is_error=True in the body): a tool error, not a
        # transport failure — see docs/22_mcp tool-vs-transport error table.
        result = ToolCallResult.from_transport(
            output="file not found", is_error=True, request_id="req-1"
        )

        assert result.is_error
        assert result.error_type == "tool"
        assert result.request_id == "req-1"
        assert result.source == "mcp"

    def test_success_has_empty_error_type(self) -> None:
        result = ToolCallResult.from_transport(output="ok", is_error=False)

        assert not result.is_error
        assert result.error_type == ""
