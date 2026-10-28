"""tests/shared/test_http_transport.py

Characterization pins for HttpTransport.call()'s retry behavior on
httpx.RequestError vs httpx.TimeoutException (implementation procedure
20261013-070354_01): a non-timeout RequestError is retried exactly _RETRY_MAX
times for both write and read tools; a TimeoutException breaks after one attempt.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from shared.http_transport import (
    _WRITE_TOOLS,
    HttpTransport,
    TransportError,
)
from shared.mcp_config import McpServerConfig, StartupMode, TransportType


def _http_cfg(
    url: str = "http://127.0.0.1:8000", call_timeout_sec: float = 60.0
) -> McpServerConfig:
    return McpServerConfig(
        transport=TransportType.HTTP,
        url=url,
        call_timeout_sec=call_timeout_sec,
        auth_token="test-token",
        startup_mode=StartupMode.PERSISTENT,
    )


@pytest.mark.asyncio
async def test_request_error_retried_three_times_for_write_and_read_tool() -> None:
    # Membership pins: the two names must straddle the write gate so the
    # assertion exercises the write-vs-read distinction, not two writes.
    assert "write_file" in _WRITE_TOOLS
    assert "read_text_file" not in _WRITE_TOOLS

    transport = HttpTransport(
        http=MagicMock(spec=httpx.AsyncClient),
        base_url="http://127.0.0.1:8000",
        server_key="srv",
        cfg=_http_cfg(),
    )
    mock_post = AsyncMock()
    transport._http.post = mock_post

    # Non-timeout RequestError -> always retried (3 attempts) for the write tool.
    mock_post.side_effect = httpx.ConnectError("boom")
    with pytest.raises(TransportError):
        await transport.call("write_file", {})
    assert mock_post.call_count == 3

    # ...and identically for a read tool (the removed client-side gate is gone).
    mock_post.reset_mock()
    mock_post.side_effect = httpx.ConnectError("boom")
    with pytest.raises(TransportError):
        await transport.call("read_text_file", {})
    assert mock_post.call_count == 3


@pytest.mark.asyncio
async def test_timeout_exception_retried_once() -> None:
    assert "read_text_file" not in _WRITE_TOOLS

    transport = HttpTransport(
        http=MagicMock(spec=httpx.AsyncClient),
        base_url="http://127.0.0.1:8000",
        server_key="srv",
        cfg=_http_cfg(),
    )
    mock_post = AsyncMock()
    transport._http.post = mock_post

    # TimeoutException is caught before the generic RequestError handler and
    # breaks without retry (1 attempt).
    mock_post.side_effect = httpx.TimeoutException("timed out")
    with pytest.raises(TransportError):
        await transport.call("read_text_file", {})
    assert mock_post.call_count == 1


@pytest.mark.asyncio
async def test_request_error_exhaustion_includes_cause_in_message() -> None:
    transport = HttpTransport(
        http=MagicMock(spec=httpx.AsyncClient),
        base_url="http://127.0.0.1:8000",
        server_key="srv",
        cfg=_http_cfg(),
    )
    mock_post = AsyncMock()
    transport._http.post = mock_post
    mock_post.side_effect = httpx.ConnectError("boom")
    with pytest.raises(TransportError) as exc:
        await transport.call("read_text_file", {})
    assert mock_post.call_count == 3
    message = str(exc.value)
    assert "Retry exhausted" in message
    assert "ConnectError" in message
    assert "boom" in message


@pytest.mark.asyncio
async def test_request_error_then_success_returns_result() -> None:
    transport = HttpTransport(
        http=MagicMock(spec=httpx.AsyncClient),
        base_url="http://127.0.0.1:8000",
        server_key="srv",
        cfg=_http_cfg(),
    )
    mock_post = AsyncMock()
    transport._http.post = mock_post
    req = httpx.Request("POST", "http://127.0.0.1:8000/v1/call_tool")
    mock_post.side_effect = [
        httpx.ConnectError("boom"),
        httpx.Response(200, request=req, json={"result": "ok", "is_error": False}),
    ]
    result = await transport.call("read_text_file", {})
    assert mock_post.call_count == 2
    assert result.output == "ok"
