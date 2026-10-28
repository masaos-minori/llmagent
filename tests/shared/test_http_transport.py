"""tests/shared/test_http_transport.py

Characterization pins for HttpTransport.call()'s retry behavior on
httpx.RequestError vs httpx.TimeoutException (implementation procedure
20261013-070354_01): a non-timeout RequestError is retried exactly _RETRY_MAX
times for both write and read tools; a TimeoutException breaks after one attempt.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from mcp_servers.dispatch import _write_tools
from shared.http_transport import (
    _AMBIGUOUS_RETRY_STATUSES,
    _PRESEND_SAFE_ERRORS,
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
async def test_request_error_exhaustion_message_contains_cause() -> None:
    transport = HttpTransport(
        http=MagicMock(spec=httpx.AsyncClient),
        base_url="http://127.0.0.1:8000",
        server_key="srv",
        cfg=_http_cfg(),
    )
    mock_post = AsyncMock()
    transport._http.post = mock_post
    mock_post.side_effect = httpx.ConnectError("connect refused")
    with pytest.raises(TransportError) as excinfo:
        await transport.call("write_file", {})
    msg = str(excinfo.value)
    assert "Retry exhausted" in msg
    assert "tool=write_file" in msg
    assert "ConnectError" in msg
    assert "connect refused" in msg
    assert "after 3 attempts" in msg
    assert mock_post.call_count == 3


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
    ok = MagicMock()
    ok.status_code = 200
    ok.raise_for_status.return_value = None
    # parse_http_json() reads resp.content; fake body mirrors the proven
    # success-after-error shape in tests/shared/test_tool_executor.py.
    ok.content = b'{"result": "done", "is_error": false}'
    ok.headers = {}
    mock_post.side_effect = [httpx.ConnectError("flaky"), ok]
    result = await transport.call("read_text_file", {})
    assert result.is_error is False
    assert mock_post.call_count == 2


@pytest.mark.asyncio
async def test_ambiguous_request_error_not_retried_for_write_tool() -> None:
    assert "write_file" in _WRITE_TOOLS
    assert "read_text_file" not in _WRITE_TOOLS
    assert httpx.ConnectError in _PRESEND_SAFE_ERRORS

    transport = HttpTransport(
        http=MagicMock(spec=httpx.AsyncClient),
        base_url="http://127.0.0.1:8000",
        server_key="srv",
        cfg=_http_cfg(),
    )
    mock_post = AsyncMock()
    transport._http.post = mock_post

    # Post-send ambiguous error on a write tool -> single attempt, fail-closed.
    # The message names the tool, the exception class, and the attempt number.
    mock_post.side_effect = httpx.ReadError("boom")
    with pytest.raises(TransportError, match="write_file") as excinfo:
        await transport.call("write_file", {})
    assert mock_post.call_count == 1
    assert "ReadError" in str(excinfo.value)


@pytest.mark.asyncio
async def test_post_send_request_error_retried_for_read_tool() -> None:
    assert "read_text_file" not in _WRITE_TOOLS

    transport = HttpTransport(
        http=MagicMock(spec=httpx.AsyncClient),
        base_url="http://127.0.0.1:8000",
        server_key="srv",
        cfg=_http_cfg(),
    )
    mock_post = AsyncMock()
    transport._http.post = mock_post

    # Read tools keep the pre-mcpinv001 retry path unchanged (REQ-004).
    mock_post.side_effect = httpx.RemoteProtocolError("boom")
    with pytest.raises(TransportError):
        await transport.call("read_text_file", {})
    assert mock_post.call_count == 3


@pytest.mark.asyncio
@pytest.mark.parametrize("status", sorted(_AMBIGUOUS_RETRY_STATUSES))
async def test_ambiguous_status_not_retried_for_write_tool(status: int) -> None:
    assert "write_file" in _WRITE_TOOLS

    transport = HttpTransport(
        http=MagicMock(spec=httpx.AsyncClient),
        base_url="http://127.0.0.1:8000",
        server_key="srv",
        cfg=_http_cfg(),
    )
    mock_post = AsyncMock()
    transport._http.post = mock_post
    resp = MagicMock()
    resp.status_code = status

    mock_post.side_effect = [resp]
    with pytest.raises(TransportError, match=str(status)):
        await transport.call("write_file", {})
    assert mock_post.call_count == 1


@pytest.mark.asyncio
async def test_429_retried_for_write_tool() -> None:
    assert "write_file" in _WRITE_TOOLS
    assert 429 not in _AMBIGUOUS_RETRY_STATUSES

    transport = HttpTransport(
        http=MagicMock(spec=httpx.AsyncClient),
        base_url="http://127.0.0.1:8000",
        server_key="srv",
        cfg=_http_cfg(),
    )
    mock_post = AsyncMock()
    transport._http.post = mock_post
    resp = MagicMock()
    resp.status_code = 429

    mock_post.side_effect = [resp, resp, resp]
    with patch("shared.http_transport.asyncio.sleep"):
        with pytest.raises(TransportError):
            await transport.call("write_file", {})
    assert mock_post.call_count == 3


def test_write_tools_mirror_dispatch_write_tools() -> None:
    assert frozenset(_write_tools) == _WRITE_TOOLS
