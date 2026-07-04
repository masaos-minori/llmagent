"""Integration tests: Agent Loop <-> MCP Servers (TC-A01 through TC-A12).

Tests exercise ToolExecutor and HttpTransport at the integration boundary.
HTTP calls use respx for transport-level mocking.

Custom tool names (prefixed with _int_) are used so that ToolRouteResolver
config_map takes priority over the tool registry (which knows only the
production tool names in tool_constants.py).
"""

from __future__ import annotations

import asyncio

import httpx
import pytest
import respx
import shared.plugin_registry as plugin_registry
from shared.mcp_config import McpServerConfig, McpServerHealthRegistry, TransportType
from shared.tool_executor import ToolExecutor

_TEST_URL = "http://127.0.0.1:19001"
_HTTP_KEY = "int_http"
_HTTP_TOOL = "_int_http_tool"


def _make_http_executor(http: httpx.AsyncClient) -> ToolExecutor:
    cfg = McpServerConfig(
        transport=TransportType.HTTP,
        url=_TEST_URL,
        tool_names=[_HTTP_TOOL],
    )
    executor = ToolExecutor(
        http=http,
        cache_ttl=0,
        server_configs={_HTTP_KEY: cfg},
        discovery_map={_HTTP_TOOL: _HTTP_KEY},
    )
    executor._resolver.resolve = lambda _: _HTTP_KEY
    return executor


# ── TC-A01: HTTP tool call succeeds ──────────────────────────────────────────


@pytest.mark.asyncio
async def test_a01_http_tool_call_succeeds():
    with respx.mock(base_url=_TEST_URL) as mock:
        mock.post("/v1/call_tool").respond(
            200, json={"result": "ok", "is_error": False}
        )
        async with httpx.AsyncClient() as http:
            executor = _make_http_executor(http)
            result = await executor.execute(_HTTP_TOOL, {"path": "/tmp/x"})

    assert not result.is_error
    assert result.output == "ok"
    assert result.server_key == _HTTP_KEY


# ── TC-A02: HTTP 504 gateway timeout → TransportError ───────────────────────


@pytest.mark.asyncio
async def test_a02_http_504_returns_transport_error():
    with respx.mock(base_url=_TEST_URL, assert_all_called=False) as mock:
        mock.post("/v1/call_tool").respond(504)
        async with httpx.AsyncClient() as http:
            executor = _make_http_executor(http)
            result = await executor.execute(_HTTP_TOOL, {})

    assert result.is_error
    assert result.error_type == "transport"
    assert executor.stat_transport_errors.get(_HTTP_KEY, 0) == 1


# ── TC-A03: HTTP timeout → TransportError, no retry ─────────────────────────


@pytest.mark.asyncio
async def test_a03_http_timeout_returns_transport_error():
    with respx.mock(base_url=_TEST_URL, assert_all_called=False) as mock:
        mock.post("/v1/call_tool").mock(side_effect=httpx.TimeoutException("timed out"))
        async with httpx.AsyncClient() as http:
            executor = _make_http_executor(http)
            result = await executor.execute(_HTTP_TOOL, {})

    assert result.is_error
    assert result.error_type == "transport"


# ── TC-A04: HTTP 503 → retry → success ──────────────────────────────────────


@pytest.mark.asyncio
async def test_a04_http_503_retry_then_success():
    call_count = 0

    def _side_effect(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count < 3:
            return httpx.Response(503)
        return httpx.Response(200, json={"result": "recovered", "is_error": False})

    with respx.mock(base_url=_TEST_URL, assert_all_called=False) as mock:
        mock.post("/v1/call_tool").mock(side_effect=_side_effect)
        async with httpx.AsyncClient() as http:
            executor = _make_http_executor(http)
            result = await executor.execute(_HTTP_TOOL, {})

    assert not result.is_error
    assert result.output == "recovered"
    assert executor.stat_transport_errors.get(_HTTP_KEY, 0) == 0


# ── TC-A05: HTTP tool error (is_error=True) → stat_tool_errors incremented ──


@pytest.mark.asyncio
async def test_a05_http_tool_error_increments_stat():
    with respx.mock(base_url=_TEST_URL) as mock:
        mock.post("/v1/call_tool").respond(
            200, json={"result": "file not found", "is_error": True}
        )
        async with httpx.AsyncClient() as http:
            executor = _make_http_executor(http)
            result = await executor.execute(_HTTP_TOOL, {})

    assert result.is_error
    assert result.error_type == "tool"
    assert executor.stat_tool_errors.get(_HTTP_KEY, 0) == 1
    assert executor.stat_transport_errors.get(_HTTP_KEY, 0) == 0


# ── TC-A10: Health check fails → call rejected without transport call ─────────


@pytest.mark.asyncio
async def test_a10_health_check_unavailable_rejects_call():
    with respx.mock(base_url=_TEST_URL, assert_all_called=False) as mock:
        transport_route = mock.post("/v1/call_tool").respond(
            200, json={"result": "ok", "is_error": False}
        )
        async with httpx.AsyncClient() as http:
            executor = _make_http_executor(http)
            health = McpServerHealthRegistry()
            executor.set_health_registry(health)
            for _ in range(3):
                health.record_failure(_HTTP_KEY)

            result = await executor.execute(_HTTP_TOOL, {})

    assert result.is_error
    assert not transport_route.called


# ── TC-A11: Plugin tool write error → ToolCallResult(is_error=True) ──────────


@pytest.mark.asyncio
async def test_a11_plugin_tool_error_does_not_propagate():
    plugin_registry._reset_for_testing()
    try:

        @plugin_registry.register_tool("_test_failing_plugin")
        async def _failing_handler(args: dict) -> tuple[str, bool]:
            raise RuntimeError("exploded")

        async with httpx.AsyncClient() as http:
            executor = _make_http_executor(http)
            result = await executor.execute("_test_failing_plugin", {})

        assert result.is_error
        assert "plugin error" in result.output
    finally:
        plugin_registry._reset_for_testing()


# ── TC-A12: Concurrent HTTP calls — all 5 complete ───────────────────────────


@pytest.mark.asyncio
async def test_a12_concurrent_http_calls_all_complete():
    with respx.mock(base_url=_TEST_URL) as mock:
        mock.post("/v1/call_tool").respond(
            200, json={"result": "ok", "is_error": False}
        )
        async with httpx.AsyncClient() as http:
            executor = _make_http_executor(http)
            results = await asyncio.gather(
                *[executor.execute(_HTTP_TOOL, {"n": i}) for i in range(5)]
            )

    assert len(results) == 5
    assert all(not r.is_error for r in results)


# ── TC-A13: HTTP 429 → retry → TransportError after 3 attempts ───────────────


@pytest.mark.asyncio
async def test_a13_http_429_retry_then_transport_error():
    call_count = 0

    def _side_effect(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(429)

    with respx.mock(base_url=_TEST_URL, assert_all_called=False) as mock:
        mock.post("/v1/call_tool").mock(side_effect=_side_effect)
        async with httpx.AsyncClient() as http:
            executor = _make_http_executor(http)
            result = await executor.execute(_HTTP_TOOL, {})

    assert result.is_error
    assert result.error_type == "transport"
    assert call_count == 3  # 3 attempts before TransportError


# ── TC-A14: HTTP 502 → retry → TransportError after 3 attempts ───────────────


@pytest.mark.asyncio
async def test_a14_http_502_retry_then_transport_error():
    call_count = 0

    def _side_effect(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        return httpx.Response(502)

    with respx.mock(base_url=_TEST_URL, assert_all_called=False) as mock:
        mock.post("/v1/call_tool").mock(side_effect=_side_effect)
        async with httpx.AsyncClient() as http:
            executor = _make_http_executor(http)
            result = await executor.execute(_HTTP_TOOL, {})

    assert result.is_error
    assert result.error_type == "transport"
    assert call_count == 3


# ── TC-A15: HTTP 400 → immediate TransportError (non-retryable) ──────────────


@pytest.mark.asyncio
async def test_a15_http_400_non_retryable():
    with respx.mock(base_url=_TEST_URL, assert_all_called=False) as mock:
        mock.post("/v1/call_tool").respond(400)
        async with httpx.AsyncClient() as http:
            executor = _make_http_executor(http)
            result = await executor.execute(_HTTP_TOOL, {})

    assert result.is_error
    assert result.error_type == "transport"
    # 400 is not in the retryable set — no retry occurs
    assert executor.stat_transport_errors.get(_HTTP_KEY, 0) == 1


# ── TC-A16: HTTP 500 → immediate TransportError (non-retryable) ──────────────


@pytest.mark.asyncio
async def test_a16_http_500_non_retryable():
    with respx.mock(base_url=_TEST_URL, assert_all_called=False) as mock:
        mock.post("/v1/call_tool").respond(500)
        async with httpx.AsyncClient() as http:
            executor = _make_http_executor(http)
            result = await executor.execute(_HTTP_TOOL, {})

    assert result.is_error
    assert result.error_type == "transport"
    # 500 is not in the retryable set — no retry occurs
    assert executor.stat_transport_errors.get(_HTTP_KEY, 0) == 1


# ── TC-A17: HTTP 503 → retry → success on 2nd attempt ────────────────────────


@pytest.mark.asyncio
async def test_a17_http_503_retry_then_success():
    call_count = 0

    def _side_effect(request: httpx.Request) -> httpx.Response:
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return httpx.Response(503)
        return httpx.Response(200, json={"result": "recovered", "is_error": False})

    with respx.mock(base_url=_TEST_URL, assert_all_called=False) as mock:
        mock.post("/v1/call_tool").mock(side_effect=_side_effect)
        async with httpx.AsyncClient() as http:
            executor = _make_http_executor(http)
            result = await executor.execute(_HTTP_TOOL, {})

    assert not result.is_error
    assert result.output == "recovered"
    assert call_count == 2  # retry succeeded on 2nd attempt
