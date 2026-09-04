"""tests/shared/test_tool_transport_invoker_merge.py
Characterization pin for ToolTransportInvoker.invoke()'s success/
TransportError recording behavior, ahead of the _invoke_and_record merge
with ToolExecutor._raw_execute. Complements test_tool_transport_invoker.py.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, call

import httpx
import pytest
from shared.http_transport import TransportError
from shared.mcp_config import McpServerConfig, TransportType
from shared.tool_transport_invoker import ToolTransportInvoker
from shared.transport_dto import ToolCallResult


def _http_cfg(url: str = "http://127.0.0.1:8000") -> McpServerConfig:
    return McpServerConfig(
        transport=TransportType.HTTP, url=url, auth_token="test-token"
    )


def _make_invoker(
    configs: dict[str, McpServerConfig] | None = None,
) -> ToolTransportInvoker:
    http = MagicMock(spec=httpx.AsyncClient)
    return ToolTransportInvoker(
        http=http,
        server_configs=configs or {"srv": _http_cfg()},
    )


class TestInvokeAndRecordMerge:
    @pytest.mark.asyncio
    async def test_invoke_success_records_once_with_result(self) -> None:
        invoker = _make_invoker()
        expected = ToolCallResult(
            output="ok",
            is_error=False,
            request_id="r1",
            server_key="srv",
            source="mcp",
        )
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(return_value=expected)
        invoker._transports["srv"] = mock_transport  # type: ignore[assignment]  # AsyncMock duck-types HttpTransport — AsyncMock
        invoker._record_success = MagicMock()  # type: ignore[method-assign]  # spy mock for _record_success — test helper

        result = await invoker.invoke("srv", "some_tool", {})

        assert result is expected
        invoker._record_success.assert_called_once_with("srv", expected)
        assert invoker._record_success.call_args == call("srv", expected)

    @pytest.mark.asyncio
    async def test_invoke_transport_error_records_once_and_returns_its_result(
        self,
    ) -> None:
        invoker = _make_invoker()
        exc = TransportError("boom")
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(side_effect=exc)
        invoker._transports["srv"] = mock_transport  # type: ignore[assignment]  # AsyncMock duck-types HttpTransport — AsyncMock
        sentinel = ToolCallResult(
            output="boom",
            is_error=True,
            request_id="",
            server_key="srv",
            source="mcp",
            error_type="transport",
        )
        invoker._record_transport_error = MagicMock(return_value=sentinel)  # type: ignore[method-assign]  # spy mock for _record_transport_error — test helper

        result = await invoker.invoke("srv", "some_tool", {})

        assert result is sentinel
        invoker._record_transport_error.assert_called_once_with("srv", exc)
        assert invoker._record_transport_error.call_args == call("srv", exc)
