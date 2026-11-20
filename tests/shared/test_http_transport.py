"""tests/shared/test_http_transport.py

Characterization pins for HttpTransport.call()'s retry behavior on
httpx.RequestError vs httpx.TimeoutException (implementation procedure
20261013-070354_01): a non-timeout RequestError is retried exactly _RETRY_MAX
times for both write and read tools; a TimeoutException breaks after one attempt.

Logical-id pins (mcpdl001 REQ-003, row 26): the outbound X-Idempotency-Key is
the context's opaque call_id — two calls with identical args send different
values, a retry re-sends the identical value, and a call with no context (or
an empty call_id) is refused before any HTTP request (AC-3). The removed
derivation tests and the HEAD_KEY literal pin (wfaudit002) are gone with
derive_idempotency_key.
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
from shared.transport_dto import ToolExecutionContext


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


def _ctx(
    name: str, call_id: str = "018f7e2c-1c3d-7abc-8def-0123456789ab"
) -> ToolExecutionContext:
    """Fixture context: opaque uuid7-shaped logical ids replace derived keys."""
    return ToolExecutionContext(
        call_id=call_id, tool=name, args_hash="args-hash", operation="call_tool"
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
    with pytest.raises(TransportError) as excinfo:
        await transport.call("write_file", {}, _ctx("write_file"))
    assert mock_post.call_count == 3
    # Pre-send safe-error exhaustion: nothing was confirmed sent (AC-6).
    assert excinfo.value.stage == ""

    # ...and identically for a read tool (the removed client-side gate is gone).
    mock_post.reset_mock()
    mock_post.side_effect = httpx.ConnectError("boom")
    with pytest.raises(TransportError):
        await transport.call("read_text_file", {}, _ctx("read_text_file"))
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
    # breaks without retry (1 attempt). The request left the client: stage="sent".
    mock_post.side_effect = httpx.TimeoutException("timed out")
    with pytest.raises(TransportError) as excinfo:
        await transport.call("read_text_file", {}, _ctx("read_text_file"))
    assert mock_post.call_count == 1
    assert excinfo.value.stage == "sent"


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
        await transport.call("write_file", {}, _ctx("write_file"))
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
    ctx = _ctx("read_text_file")
    result = await transport.call("read_text_file", {}, ctx)
    assert result.is_error is False
    assert mock_post.call_count == 2
    # A returned result means a response was received, and it carries the
    # call's identity (AC-2 end-to-end pin).
    assert result.dispatch_stage == "response"
    assert result.context is ctx


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
    # Post-send ambiguity: stage="sent" (the request reached the wire).
    mock_post.side_effect = httpx.ReadError("boom")
    with pytest.raises(TransportError, match="write_file") as excinfo:
        await transport.call("write_file", {}, _ctx("write_file"))
    assert mock_post.call_count == 1
    assert "ReadError" in str(excinfo.value)
    assert excinfo.value.stage == "sent"


@pytest.mark.asyncio
async def test_ambiguous_request_error_not_retried_for_mdq_write_tool() -> None:
    """MDQ writes hit the fail-closed gate via the canonical set (REQ-003)."""
    assert "index_paths" in _WRITE_TOOLS
    assert "refresh_index" in _WRITE_TOOLS

    transport = HttpTransport(
        http=MagicMock(spec=httpx.AsyncClient),
        base_url="http://127.0.0.1:8000",
        server_key="srv",
        cfg=_http_cfg(),
    )
    mock_post = AsyncMock()
    transport._http.post = mock_post

    # Post-send ambiguous error on an MDQ write -> single attempt, fail-closed,
    # consistent with dispatch.py dedup membership.
    mock_post.side_effect = httpx.ReadError("boom")
    with pytest.raises(TransportError, match="index_paths"):
        await transport.call("index_paths", {}, _ctx("index_paths"))
    assert mock_post.call_count == 1


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
        await transport.call("read_text_file", {}, _ctx("read_text_file"))
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
    with pytest.raises(TransportError, match=str(status)) as excinfo:
        await transport.call("write_file", {}, _ctx("write_file"))
    assert mock_post.call_count == 1
    # An HTTP response was received: stage="response" (AC-6).
    assert excinfo.value.stage == "response"


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
            await transport.call("write_file", {}, _ctx("write_file"))
    assert mock_post.call_count == 3


def test_write_tools_mirror_dispatch_write_tools() -> None:
    assert frozenset(_write_tools) == _WRITE_TOOLS


class TestLogicalCallIdHeader:
    """mcpdl001 REQ-003 (AC-1/AC-2/AC-3): the wire key is the opaque logical id."""

    @staticmethod
    def _success_transport() -> tuple[HttpTransport, AsyncMock]:
        transport = HttpTransport(
            http=MagicMock(spec=httpx.AsyncClient),
            base_url="http://127.0.0.1:8000",
            server_key="srv",
            cfg=_http_cfg(),
        )
        mock_post = AsyncMock()
        resp = MagicMock()
        resp.status_code = 200
        resp.content = b'{"result":"ok","is_error":false}'
        resp.raise_for_status = MagicMock()
        resp.headers = {}
        mock_post.return_value = resp
        transport._http.post = mock_post
        return transport, mock_post

    @pytest.mark.asyncio
    async def test_identical_args_send_different_headers(self) -> None:
        """Two logical calls with byte-identical args never collide on the wire key."""
        transport_a, post_a = self._success_transport()
        transport_b, post_b = self._success_transport()
        await transport_a.call(
            "write_file",
            {"path": "/p"},
            _ctx("write_file", "018f0000-0000-7000-8000-000000000001"),
        )
        await transport_b.call(
            "write_file",
            {"path": "/p"},
            _ctx("write_file", "018f0000-0000-7000-8000-000000000002"),
        )
        key_a = post_a.call_args.kwargs["headers"]["X-Idempotency-Key"]
        key_b = post_b.call_args.kwargs["headers"]["X-Idempotency-Key"]
        assert key_a != key_b

    @pytest.mark.asyncio
    async def test_retry_resends_identical_header(self) -> None:
        """One logical call re-sends the identical call_id across every retry (AC-1)."""
        transport = HttpTransport(
            http=MagicMock(spec=httpx.AsyncClient),
            base_url="http://127.0.0.1:8000",
            server_key="srv",
            cfg=_http_cfg(),
        )
        mock_post = AsyncMock()
        ok = MagicMock()
        ok.status_code = 200
        ok.content = b'{"result":"ok","is_error":false}'
        ok.raise_for_status = MagicMock()
        ok.headers = {}
        mock_post.side_effect = [httpx.ConnectError("flaky"), ok]
        transport._http.post = mock_post
        call_id = "018f0000-0000-7000-8000-000000000003"
        await transport.call("write_file", {"path": "/p"}, _ctx("write_file", call_id))
        sent = [
            c.kwargs["headers"]["X-Idempotency-Key"] for c in mock_post.call_args_list
        ]
        assert sent == [call_id, call_id]

    @pytest.mark.asyncio
    async def test_header_and_result_carry_the_call_id(self) -> None:
        """AC-2 end-to-end pin: header == context.call_id, result carries the context."""
        transport, mock_post = self._success_transport()
        ctx = _ctx("read_text_file", "018f0000-0000-7000-8000-000000000004")
        result = await transport.call("read_text_file", {"path": "/x"}, ctx)
        assert mock_post.call_args.kwargs["headers"]["X-Idempotency-Key"] == ctx.call_id
        assert result.context is ctx
        assert result.dispatch_stage == "response"
        assert result.is_error is False

    @pytest.mark.asyncio
    async def test_no_context_refused_before_any_http_request(self) -> None:
        """AC-3 gate: no context -> refused result, zero HTTP attempts."""
        transport, mock_post = self._success_transport()
        result = await transport.call("write_file", {"path": "/p"})
        assert mock_post.await_count == 0
        assert result.is_error is True
        assert result.error_type == "routing"
        assert result.dispatch_stage == ""
        assert result.context is None
        assert "no logical call id" in result.output

    @pytest.mark.asyncio
    async def test_empty_call_id_refused_before_any_http_request(self) -> None:
        """AC-3 gate: a context with an empty call_id is refused the same way."""
        transport, mock_post = self._success_transport()
        empty_ctx = ToolExecutionContext(
            call_id="", tool="write_file", args_hash="h", operation="call_tool"
        )
        result = await transport.call("write_file", {"path": "/p"}, empty_ctx)
        assert mock_post.await_count == 0
        assert result.is_error is True
        assert result.error_type == "routing"
        assert result.dispatch_stage == ""
        assert result.context is empty_ctx

    @pytest.mark.asyncio
    async def test_session_and_auth_headers_unchanged(self) -> None:
        """X-Session-Id/Authorization construction stays unchanged (REQ-003 scope)."""
        transport, mock_post = self._success_transport()
        transport.set_session_id("sess-pin")
        await transport.call("write_file", {"path": "/p"}, _ctx("write_file"))
        headers = mock_post.call_args.kwargs["headers"]
        assert headers["X-Session-Id"] == "sess-pin"
        assert headers["Authorization"] == "Bearer test-token"


class TestToolLevelStatusClassification:
    """Tool-level statuses return tool results; transport statuses still raise
    (healthcascade001 REQ-001/REQ-003/REQ-004)."""

    @staticmethod
    def _make_transport() -> tuple[HttpTransport, AsyncMock]:
        transport = HttpTransport(
            http=MagicMock(spec=httpx.AsyncClient),
            base_url="http://127.0.0.1:8000",
            server_key="srv",
            cfg=_http_cfg(),
        )
        mock_post = AsyncMock()
        transport._http.post = mock_post
        return transport, mock_post

    @staticmethod
    def _json_resp(status: int, body: bytes) -> MagicMock:
        resp = MagicMock()
        resp.status_code = status
        resp.content = body
        resp.text = body.decode("utf-8")
        resp.headers = {"x-request-id": "req-1"}
        return resp

    @pytest.mark.asyncio
    @pytest.mark.parametrize("status", [400, 403, 404, 409, 422])
    async def test_tool_level_status_returns_tool_error_result(
        self, status: int
    ) -> None:
        transport, mock_post = self._make_transport()
        mock_post.side_effect = [self._json_resp(status, b'{"detail": "no such file"}')]
        result = await transport.call(
            "read_text_file", {"path": "/tmp/missing"}, _ctx("read_text_file")
        )
        assert result.is_error is True
        assert result.error_type == "tool"
        assert "no such file" in result.output
        assert result.server_key == "srv"
        assert result.request_id == "req-1"
        assert result.dispatch_stage == "response"

    @pytest.mark.asyncio
    async def test_tool_level_status_with_result_body(self) -> None:
        transport, mock_post = self._make_transport()
        mock_post.side_effect = [
            self._json_resp(403, b'{"result": "denied by policy"}'),
        ]
        result = await transport.call(
            "write_file", {"path": "/etc/passwd"}, _ctx("write_file")
        )
        assert result.is_error is True
        assert result.error_type == "tool"
        assert "denied by policy" in result.output

    @pytest.mark.asyncio
    async def test_tool_level_status_with_malformed_body(self) -> None:
        transport, mock_post = self._make_transport()
        mock_post.side_effect = [self._json_resp(422, b"not-json")]
        result = await transport.call("shell_run", {"command": "ls"}, _ctx("shell_run"))
        assert result.is_error is True
        assert result.error_type == "tool"
        assert "not-json" in result.output

    @pytest.mark.asyncio
    async def test_401_still_transport_error(self) -> None:
        transport, mock_post = self._make_transport()
        resp = self._json_resp(401, b'{"detail": "unauthorized"}')
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "401", request=MagicMock(), response=resp
        )
        mock_post.side_effect = [resp]
        with pytest.raises(TransportError) as excinfo:
            await transport.call("read_text_file", {}, _ctx("read_text_file"))
        assert mock_post.call_count == 1
        assert excinfo.value.stage == "response"

    @pytest.mark.asyncio
    async def test_5xx_still_transport_error(self) -> None:
        transport, mock_post = self._make_transport()
        resp = self._json_resp(500, b'{"detail": "internal error"}')
        resp.raise_for_status.side_effect = httpx.HTTPStatusError(
            "500", request=MagicMock(), response=resp
        )
        mock_post.side_effect = [resp]
        with pytest.raises(TransportError) as excinfo:
            await transport.call("read_text_file", {}, _ctx("read_text_file"))
        assert mock_post.call_count == 1
        assert excinfo.value.stage == "response"

    @pytest.mark.asyncio
    async def test_write_tool_ambiguous_status_gate_unchanged(self) -> None:
        transport, mock_post = self._make_transport()
        resp = MagicMock()
        resp.status_code = 503
        mock_post.side_effect = [resp]
        with pytest.raises(TransportError, match="retry suppressed"):
            await transport.call("write_file", {}, _ctx("write_file"))
        assert mock_post.call_count == 1
