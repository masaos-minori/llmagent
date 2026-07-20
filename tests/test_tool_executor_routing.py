"""tests/test_tool_executor_routing.py
Unit tests for ToolExecutor: resolver integration, lifecycle injection,
set_lifecycle(), transport-dispatch paths, and auth header injection.
"""

from __future__ import annotations

import re
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from shared.http_transport import HttpTransport, TransportError
from shared.mcp_config import (
    McpServerConfig,
    McpServerHealthRegistry,
    McpServerHealthState,
    StartupMode,
    TransportType,
)
from shared.runtime_tool import build_runtime_tool
from shared.runtime_tool_registry import RuntimeToolRegistry
from shared.tool_executor import LifecycleProtocol, ToolExecutor
from shared.transport_dto import ToolCallResult


def _http_cfg(url: str = "http://127.0.0.1:8000") -> McpServerConfig:
    return McpServerConfig(
        transport=TransportType.HTTP, url=url, startup_mode=StartupMode.PERSISTENT
    )


def _runtime_registry_for(tool_to_server: dict[str, str]) -> RuntimeToolRegistry:
    """Build a RuntimeToolRegistry covering the given {tool_name: server_key} pairs."""
    tools = {
        name: build_runtime_tool(
            name=name,
            server_key=server_key,
            status="active",
            is_write=False,
            requires_serial=False,
            resource_scope="",
            agent_safety_tier="READ_ONLY",
            requires_approval=False,
            enabled_for_llm=True,
            capabilities=(),
        )
        for name, server_key in tool_to_server.items()
    }
    return RuntimeToolRegistry(tools=tools)


# Tool routes this test file exercises via ex.execute()/ex._raw_execute(); wired into
# each executor's resolver via set_runtime_registry() to mirror the production flow
# where ToolExecutor.set_runtime_registry() is called after discovery completes.
_DEFAULT_TEST_TOOL_ROUTES = {
    "read_text_file": "file_read",
    "trigger_workflow": "cicd",
}


def _make_executor(
    configs: dict[str, McpServerConfig] | None = None,
    concurrency_limits: dict[str, int] | None = None,
) -> ToolExecutor:
    resolved_configs = configs or {"file_read": _http_cfg()}
    http = MagicMock(spec=httpx.AsyncClient)
    ex = ToolExecutor(
        http,
        cache_ttl=60.0,
        server_configs=resolved_configs,
        concurrency_limits=concurrency_limits,
    )
    routes = {
        tool: server
        for tool, server in _DEFAULT_TEST_TOOL_ROUTES.items()
        if server in resolved_configs
    }
    if routes:
        ex.set_runtime_registry(_runtime_registry_for(routes))
    return ex


class TestResolverIntegration:
    def test_resolver_resolves_via_runtime_registry(self) -> None:
        ex = _make_executor({"file_read": _http_cfg()})
        assert ex._resolver.resolve("read_text_file") == "file_read"

    def test_resolver_raises_for_unknown_tool(self) -> None:
        ex = _make_executor()
        with pytest.raises(ValueError, match="Unknown tool"):
            ex._resolver.resolve("no_such_tool")

    def test_resolver_raises_for_empty_string(self) -> None:
        ex = _make_executor()
        with pytest.raises(ValueError, match="Unknown tool"):
            ex._resolver.resolve("")

    def test_resolver_raises_for_tool_call_id_format(self) -> None:
        ex = _make_executor()
        with pytest.raises(ValueError, match="Unknown tool"):
            ex._resolver.resolve("call_abc123")

    def test_resolver_raises_for_none_input(self) -> None:
        ex = _make_executor()
        with pytest.raises((AttributeError, TypeError, ValueError)):
            ex._resolver.resolve(None)

    def test_concurrency_limits_unknown_key_warns(self, caplog: Any) -> None:
        import logging

        with caplog.at_level(logging.WARNING, logger="shared.tool_executor"):
            _make_executor(
                configs={"file_read": _http_cfg()},
                concurrency_limits={"totally_unknown": 2},
            )
        assert "unknown server key" in caplog.text.lower()
        assert "for these server keys" in caplog.text.lower()

    def test_concurrency_limits_known_key_no_warning(self, caplog: Any) -> None:
        import logging

        with caplog.at_level(logging.WARNING, logger="shared.tool_executor"):
            _make_executor(
                configs={"file_read": _http_cfg()},
                concurrency_limits={"file_read": 2},
            )
        assert "unknown server key" not in caplog.text.lower()


class TestLifecycleProtocolIdentity:
    def test_lifecycle_protocol_is_canonical_reexport(self) -> None:
        from shared.tool_executor import LifecycleProtocol as ExecutorLP
        from shared.tool_lifecycle import LifecycleProtocol as CanonicalLP

        assert ExecutorLP is CanonicalLP


class TestSetLifecycle:
    def test_set_lifecycle_stores_instance(self) -> None:
        ex = _make_executor()
        assert ex._lifecycle is None

        mock_lc = MagicMock(spec=LifecycleProtocol)
        ex.set_lifecycle(mock_lc)
        assert ex._lifecycle is mock_lc

    def test_set_lifecycle_none_clears(self) -> None:
        ex = _make_executor()
        mock_lc = MagicMock(spec=LifecycleProtocol)
        ex.set_lifecycle(mock_lc)
        ex.set_lifecycle(None)
        assert ex._lifecycle is None


class TestRawExecuteWithLifecycle:
    @pytest.mark.asyncio
    async def test_ensure_ready_called_before_transport(self) -> None:
        http = MagicMock(spec=httpx.AsyncClient)
        configs = {"file_read": _http_cfg("http://127.0.0.1:8000")}
        ex = ToolExecutor(http, cache_ttl=60.0, server_configs=configs)
        ex.set_runtime_registry(_runtime_registry_for({"read_text_file": "file_read"}))

        call_order: list[str] = []

        mock_lc = AsyncMock(spec=LifecycleProtocol)

        async def fake_ensure(key: str) -> None:
            call_order.append(f"ensure:{key}")

        mock_lc.ensure_ready = fake_ensure
        ex.set_lifecycle(mock_lc)

        # Patch the transport to record call order
        mock_transport = AsyncMock()

        def _record_and_ok(*a: object, **kw: object) -> ToolCallResult:
            call_order.append("call")
            return ToolCallResult(
                output="ok", is_error=False, request_id="", server_key=""
            )

        mock_transport.call = AsyncMock(side_effect=_record_and_ok)
        ex._transports["file_read"] = mock_transport

        await ex._raw_execute("read_text_file", {})
        assert call_order[0] == "ensure:file_read"
        assert call_order[1] == "call"

    @pytest.mark.asyncio
    async def test_no_lifecycle_skips_ensure_ready(self) -> None:
        http = MagicMock(spec=httpx.AsyncClient)
        configs = {"file_read": _http_cfg()}
        ex = ToolExecutor(http, cache_ttl=60.0, server_configs=configs)
        ex.set_runtime_registry(_runtime_registry_for({"read_text_file": "file_read"}))
        assert ex._lifecycle is None

        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="result", is_error=False, request_id="", server_key=""
            )
        )
        ex._transports["file_read"] = mock_transport

        res = await ex._raw_execute("read_text_file", {})
        _result, is_err = res.output, res.is_error
        assert not is_err


class TestHttpTransportAuthHeader:
    @pytest.mark.asyncio
    async def test_auth_token_set_sends_bearer_header(self) -> None:
        cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:8000",
            auth_token="my-token",
        )
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = MagicMock()
        mock_resp.content = b'{"result":"ok","is_error":false}'
        mock_resp.raise_for_status = MagicMock()
        mock_resp.headers = {}
        mock_http.post = AsyncMock(return_value=mock_resp)

        transport = HttpTransport(mock_http, "http://127.0.0.1:8000", "svc", cfg)
        await transport.call("my_tool", {})

        call_kwargs = mock_http.post.call_args.kwargs
        assert call_kwargs["headers"] == {"Authorization": "Bearer my-token"}

    @pytest.mark.asyncio
    async def test_no_auth_token_sends_empty_headers(self) -> None:
        cfg = McpServerConfig(transport=TransportType.HTTP, url="http://127.0.0.1:8000")
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = MagicMock()
        mock_resp.content = b'{"result":"ok","is_error":false}'
        mock_resp.raise_for_status = MagicMock()
        mock_resp.headers = {}
        mock_http.post = AsyncMock(return_value=mock_resp)

        transport = HttpTransport(mock_http, "http://127.0.0.1:8000", "svc", cfg)
        await transport.call("my_tool", {})

        call_kwargs = mock_http.post.call_args.kwargs
        assert call_kwargs["headers"] == {}

    @pytest.mark.asyncio
    async def test_no_cfg_sends_empty_headers(self) -> None:
        """Backward-compat: HttpTransport without cfg arg sends no auth header."""
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = MagicMock()
        mock_resp.content = b'{"result":"ok","is_error":false}'
        mock_resp.raise_for_status = MagicMock()
        mock_resp.headers = {}
        mock_http.post = AsyncMock(return_value=mock_resp)

        transport = HttpTransport(mock_http, "http://127.0.0.1:8000", "svc")
        await transport.call("my_tool", {})

        call_kwargs = mock_http.post.call_args.kwargs
        assert call_kwargs["headers"] == {}

    @pytest.mark.asyncio
    async def test_x_request_id_captured_from_response_header(self) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = MagicMock()
        mock_resp.content = b'{"result":"ok","is_error":false}'
        mock_resp.raise_for_status = MagicMock()
        mock_resp.headers = {"x-request-id": "abc-123"}
        mock_http.post = AsyncMock(return_value=mock_resp)

        transport = HttpTransport(mock_http, "http://127.0.0.1:8000", "svc")
        res = await transport.call("my_tool", {})
        x_req_id = res.request_id

        assert x_req_id == "abc-123"

    @pytest.mark.asyncio
    async def test_x_request_id_empty_when_header_absent(self) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = MagicMock()
        mock_resp.content = b'{"result":"ok","is_error":false}'
        mock_resp.raise_for_status = MagicMock()
        mock_resp.headers = {}
        mock_http.post = AsyncMock(return_value=mock_resp)

        transport = HttpTransport(mock_http, "http://127.0.0.1:8000", "svc")
        res = await transport.call("my_tool", {})
        x_req_id = res.request_id

        assert x_req_id == ""


class TestHttpTransportErrors:
    @pytest.mark.asyncio
    async def test_http_status_error_raises_transport_error(self) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        req = httpx.Request("POST", "http://127.0.0.1:8000/v1/call_tool")
        resp_obj = httpx.Response(500, request=req)
        mock_http.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "server error", request=req, response=resp_obj
            )
        )
        transport = HttpTransport(mock_http, "http://127.0.0.1:8000", "svc")
        with pytest.raises(TransportError) as exc_info:
            await transport.call("my_tool", {})
        assert "HTTPStatusError" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_request_error_raises_transport_error(self) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        req = httpx.Request("POST", "http://127.0.0.1:8000/v1/call_tool")
        mock_http.post = AsyncMock(
            side_effect=httpx.ConnectError("refused", request=req)
        )
        transport = HttpTransport(mock_http, "http://127.0.0.1:8000", "svc")
        with pytest.raises(TransportError):
            await transport.call("my_tool", {})

    @pytest.mark.asyncio
    async def test_invalid_response_raises_transport_error(self) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        req = httpx.Request("POST", "http://127.0.0.1:8000/v1/call_tool")
        resp_obj = httpx.Response(200, request=req, content=b"not-json")
        mock_http.post = AsyncMock(return_value=resp_obj)
        transport = HttpTransport(mock_http, "http://127.0.0.1:8000", "svc")
        with pytest.raises(TransportError):
            await transport.call("my_tool", {})


class TestToolExecutorExecute:
    @pytest.mark.asyncio
    async def test_cache_hit_returns_empty_x_request_id(self) -> None:
        ex = _make_executor()
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="cached result",
                is_error=False,
                request_id="req-1",
                server_key="",
            )
        )
        ex._transports["file_read"] = mock_transport

        await ex.execute("read_text_file", {"path": "f"})
        res = await ex.execute("read_text_file", {"path": "f"})
        result, is_err, x_req = res.output, res.is_error, res.request_id
        assert result == "cached result"
        assert not is_err
        assert x_req == ""
        assert ex.stat_cache_hits == 1

    @pytest.mark.asyncio
    async def test_expired_cache_entry_is_re_executed(self) -> None:
        http = MagicMock(spec=httpx.AsyncClient)
        ex = ToolExecutor(
            http,
            cache_ttl=0.0,
            server_configs={"file_read": _http_cfg()},
        )
        ex.set_runtime_registry(_runtime_registry_for({"read_text_file": "file_read"}))
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="result", is_error=False, request_id="req-1", server_key=""
            )
        )
        ex._transports["file_read"] = mock_transport

        await ex.execute("read_text_file", {"path": "f"})
        res = await ex.execute("read_text_file", {"path": "f"})
        result, _is_err, _x_req = res.output, res.is_error, res.request_id
        assert result == "result"
        assert mock_transport.call.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_propagates_x_request_id_on_cache_miss(self) -> None:
        ex = _make_executor()
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="ok", is_error=False, request_id="req-xyz", server_key=""
            )
        )
        ex._transports["file_read"] = mock_transport

        res = await ex.execute("read_text_file", {"path": "f"})
        x_req = res.request_id
        assert x_req == "req-xyz"


class TestSetSessionId:
    @pytest.mark.asyncio
    async def test_session_id_injected_into_http_transport_header(self) -> None:
        """set_session_id() propagates X-Session-Id to all HttpTransport instances."""
        cfg = McpServerConfig(transport=TransportType.HTTP, url="http://127.0.0.1:8000")
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = MagicMock()
        mock_resp.content = b'{"result":"ok","is_error":false}'
        mock_resp.raise_for_status = MagicMock()
        mock_resp.headers = {}
        mock_http.post = AsyncMock(return_value=mock_resp)

        ex = ToolExecutor(mock_http, cache_ttl=60.0, server_configs={"srv": cfg})
        ex.set_session_id("sess-abc")

        # Trigger a call so headers are captured
        transport = ex._transports["srv"]
        assert isinstance(transport, HttpTransport)
        await transport.call("some_tool", {})

        call_kwargs = mock_http.post.call_args.kwargs
        assert call_kwargs["headers"].get("X-Session-Id") == "sess-abc"

    def test_set_session_id_empty_string_does_not_inject_header(self) -> None:
        """Empty session_id must not add X-Session-Id header."""
        cfg = McpServerConfig(transport=TransportType.HTTP, url="http://127.0.0.1:8000")
        mock_http = MagicMock(spec=httpx.AsyncClient)
        ex = ToolExecutor(mock_http, cache_ttl=60.0, server_configs={"srv": cfg})
        ex.set_session_id("")

        transport = ex._transports["srv"]
        assert isinstance(transport, HttpTransport)
        assert transport._session_id == ""


# ── apply_config ──────────────────────────────────────────────────────────────


class TestToolExecutorApplyConfig:
    def _make_executor(self) -> ToolExecutor:
        from unittest.mock import AsyncMock

        import httpx
        from shared.mcp_config import McpServerConfig, TransportType
        from shared.tool_executor import ToolExecutor

        cfg = McpServerConfig(transport=TransportType.HTTP, url="http://localhost:8005")
        return ToolExecutor(
            http=AsyncMock(spec=httpx.AsyncClient),
            cache_ttl=300.0,
            server_configs={"file_read": cfg},
        )

    def test_apply_config_cache_ttl(self) -> None:
        ex = self._make_executor()
        ex.apply_config(cache_ttl=600.0)
        assert ex._cache_ttl == 600.0

    def test_apply_config_none_is_no_op(self) -> None:
        ex = self._make_executor()
        ex.apply_config()
        assert ex._cache_ttl == 300.0

    def test_apply_config_does_not_recreate_transports_or_resolver(self) -> None:
        ex = self._make_executor()
        transports_before = ex._transports
        transport_before = ex._transports["file_read"]
        server_configs_before = ex._server_configs
        resolver_before = ex._resolver

        ex.apply_config(cache_ttl=600.0)

        assert ex._cache_ttl == 600.0
        assert ex._transports is transports_before
        assert ex._transports["file_read"] is transport_before
        assert ex._server_configs is server_configs_before
        assert ex._resolver is resolver_before


# ── McpServerHealthRegistry ───────────────────────────────────────────────────


class TestMcpServerHealthRegistry:
    def test_initial_state_is_healthy(self) -> None:
        r = McpServerHealthRegistry(failure_threshold=3)
        assert r.get_state("srv") == McpServerHealthState.HEALTHY

    def test_first_failure_is_degraded(self) -> None:
        r = McpServerHealthRegistry(failure_threshold=3)
        state = r.record_failure("srv")
        assert state == McpServerHealthState.DEGRADED
        assert r.get_state("srv") == McpServerHealthState.DEGRADED

    def test_failure_at_threshold_is_unavailable(self) -> None:
        r = McpServerHealthRegistry(failure_threshold=3)
        r.record_failure("srv")
        r.record_failure("srv")
        state = r.record_failure("srv")
        assert state == McpServerHealthState.UNAVAILABLE
        assert r.is_unavailable("srv")

    def test_success_resets_to_healthy(self) -> None:
        r = McpServerHealthRegistry(failure_threshold=3)
        r.record_failure("srv")
        r.record_failure("srv")
        r.record_failure("srv")
        r.record_success("srv")
        assert r.get_state("srv") == McpServerHealthState.HEALTHY
        assert not r.is_unavailable("srv")

    def test_success_resets_failure_count(self) -> None:
        r = McpServerHealthRegistry(failure_threshold=2)
        r.record_failure("srv")
        r.record_success("srv")
        # One more failure should be degraded, not unavailable
        r.record_failure("srv")
        assert r.get_state("srv") == McpServerHealthState.DEGRADED

    def test_is_unavailable_false_for_healthy(self) -> None:
        r = McpServerHealthRegistry()
        assert not r.is_unavailable("unknown_server")

    def test_health_registry_transitions_from_validation_plan(self) -> None:
        """Matches the validation plan test spec exactly."""
        r = McpServerHealthRegistry(failure_threshold=3)
        assert r.get_state("srv") == McpServerHealthState.HEALTHY
        r.record_failure("srv")
        assert r.get_state("srv") == McpServerHealthState.DEGRADED
        r.record_failure("srv")
        r.record_failure("srv")
        assert r.get_state("srv") == McpServerHealthState.UNAVAILABLE
        r.record_success("srv")
        assert r.get_state("srv") == McpServerHealthState.HEALTHY

    def test_half_open_cooldown_expiry_allows_trial_probe(self) -> None:
        """After cooldown elapses, is_unavailable returns False and state becomes HALF_OPEN."""
        import time as _time

        r = McpServerHealthRegistry(failure_threshold=3, half_open_cooldown_sec=0.01)
        r.record_failure("srv")
        r.record_failure("srv")
        r.record_failure("srv")
        assert r.get_state("srv") == McpServerHealthState.UNAVAILABLE
        assert r.is_unavailable("srv")
        _time.sleep(0.02)
        assert not r.is_unavailable("srv")
        assert r.get_state("srv") == McpServerHealthState.HALF_OPEN

    def test_half_open_probe_failure_resets_to_unavailable(self) -> None:
        """HALF_OPEN probe failure resets to UNAVAILABLE with fresh cooldown."""
        import time as _time

        r = McpServerHealthRegistry(failure_threshold=3, half_open_cooldown_sec=0.01)
        r.record_failure("srv")
        r.record_failure("srv")
        r.record_failure("srv")
        assert r.get_state("srv") == McpServerHealthState.UNAVAILABLE
        _time.sleep(0.02)
        assert not r.is_unavailable("srv")
        assert r.get_state("srv") == McpServerHealthState.HALF_OPEN
        state = r.record_failure("srv")
        assert state == McpServerHealthState.UNAVAILABLE
        assert r.get_state("srv") == McpServerHealthState.UNAVAILABLE
        assert r.is_unavailable("srv")

    def test_half_open_probe_success_restores_healthy(self) -> None:
        """HALF_OPEN probe success reverts to HEALTHY."""
        import time as _time

        r = McpServerHealthRegistry(failure_threshold=3, half_open_cooldown_sec=0.01)
        r.record_failure("srv")
        r.record_failure("srv")
        r.record_failure("srv")
        assert r.get_state("srv") == McpServerHealthState.UNAVAILABLE
        _time.sleep(0.02)
        assert not r.is_unavailable("srv")
        assert r.get_state("srv") == McpServerHealthState.HALF_OPEN
        r.record_success("srv")
        assert r.get_state("srv") == McpServerHealthState.HEALTHY
        assert not r.is_unavailable("srv")

    def test_half_open_cooldown_not_expired_still_unavailable(self) -> None:
        """Before cooldown elapses, is_unavailable still returns True."""
        r = McpServerHealthRegistry(failure_threshold=3, half_open_cooldown_sec=10.0)
        r.record_failure("srv")
        r.record_failure("srv")
        r.record_failure("srv")
        assert r.get_state("srv") == McpServerHealthState.UNAVAILABLE
        assert r.is_unavailable("srv")


# ── ToolExecutor startup_mode gate ──────────────────────────────────────────────


class TestToolExecutorStartupModeGate:
    @pytest.mark.asyncio
    async def test_none_mode_server_returns_error_without_transport_call(self) -> None:
        """startup_mode=none short-circuits _raw_execute before health check or transport."""
        cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:8012",
            startup_mode=StartupMode.NONE,
        )
        ex = _make_executor(configs={"cicd": cfg})

        with patch.object(ex, "_transports", {}):
            res = await ex._raw_execute("trigger_workflow", {})

        assert res.is_error
        assert "disabled" in res.output.lower()
        assert "cicd" in res.output

    @pytest.mark.asyncio
    async def test_subprocess_mode_server_proceeds_past_gate(self) -> None:
        """startup_mode=subprocess is not blocked by the startup_mode gate."""
        cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:8000",
            startup_mode=StartupMode.SUBPROCESS,
            cmd=["true"],
        )
        ex = _make_executor(configs={"file_read": cfg})
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="ok", is_error=False, request_id="req-1", server_key=""
            )
        )
        ex._transports = {"file_read": mock_transport}

        res = await ex._raw_execute("read_text_file", {})

        mock_transport.call.assert_called_once()
        assert not res.is_error

    def test_unknown_server_key_does_not_raise(self) -> None:
        """_check_startup_mode returns None (no gate) when server_key is unconfigured."""
        ex = _make_executor(configs={"file_read": _http_cfg()})
        assert ex._check_startup_mode("nonexistent") is None


# ── ToolExecutor health gate ──────────────────────────────────────────────────


class TestToolExecutorHealthGate:
    @pytest.mark.asyncio
    async def test_unavailable_server_returns_error_without_transport_call(
        self,
    ) -> None:
        """Unavailable server short-circuits _raw_execute without transport call."""
        registry = McpServerHealthRegistry(failure_threshold=1)
        registry.record_failure("file_read")

        ex = _make_executor(configs={"file_read": _http_cfg()})
        ex.set_health_registry(registry)

        with patch.object(ex, "_transports", {}):
            res = await ex._raw_execute("read_text_file", {})
        result, is_error = res.output, res.is_error

        assert is_error
        assert "unavailable" in result.lower()

    @pytest.mark.asyncio
    async def test_healthy_server_proceeds_to_transport(self) -> None:
        """Healthy server is not blocked by health gate."""
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor(configs={"file_read": _http_cfg()})
        ex.set_health_registry(registry)

        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="ok", is_error=False, request_id="req-1", server_key=""
            )
        )
        ex._transports = {"file_read": mock_transport}

        res = await ex._raw_execute("read_text_file", {})
        _result, is_error = res.output, res.is_error
        mock_transport.call.assert_called_once()
        assert not is_error

    def test_set_health_registry_stores_registry(self) -> None:
        ex = _make_executor()
        registry = McpServerHealthRegistry()
        ex.set_health_registry(registry)
        assert ex._health_registry is registry

    def test_set_health_registry_accepts_none(self) -> None:
        ex = _make_executor()
        ex.set_health_registry(None)
        assert ex._health_registry is None

    @pytest.mark.asyncio
    async def test_transport_success_calls_record_success(self) -> None:
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor(configs={"file_read": _http_cfg()})
        ex.set_health_registry(registry)
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="ok", is_error=False, request_id="", server_key="file_read"
            )
        )
        ex._transports["file_read"] = mock_transport
        res = await ex._raw_execute("read_text_file", {})
        assert not res.is_error
        assert registry.get_state("file_read") == McpServerHealthState.HEALTHY

    @pytest.mark.asyncio
    async def test_transport_failure_calls_record_failure(self) -> None:
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor(configs={"file_read": _http_cfg()})
        ex.set_health_registry(registry)
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            side_effect=TransportError("connection refused")
        )
        ex._transports["file_read"] = mock_transport
        res = await ex._raw_execute("read_text_file", {})
        assert res.is_error
        assert "connection refused" in res.output
        assert registry.get_state("file_read") == McpServerHealthState.DEGRADED

    @pytest.mark.asyncio
    async def test_repeated_failures_reach_unavailable(self) -> None:
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor(configs={"file_read": _http_cfg()})
        ex.set_health_registry(registry)
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(side_effect=TransportError("fail"))
        ex._transports["file_read"] = mock_transport
        for _ in range(3):
            await ex._raw_execute("read_text_file", {})
        assert registry.is_unavailable("file_read")

    @pytest.mark.asyncio
    async def test_unavailable_server_blocks_dispatch(self) -> None:
        registry = McpServerHealthRegistry(failure_threshold=1)
        registry.record_failure("file_read")
        ex = _make_executor(configs={"file_read": _http_cfg()})
        ex.set_health_registry(registry)
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="ok", is_error=False, request_id="", server_key=""
            )
        )
        ex._transports["file_read"] = mock_transport
        res = await ex._raw_execute("read_text_file", {})
        assert res.is_error
        assert "unavailable" in res.output.lower()
        mock_transport.call.assert_not_called()

    @pytest.mark.asyncio
    async def test_tool_error_does_not_affect_health(self) -> None:
        """Tool-level error (is_error=true from server) should NOT increment failure counter."""
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor(configs={"file_read": _http_cfg()})
        ex.set_health_registry(registry)
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="tool error",
                is_error=True,
                request_id="",
                server_key="file_read",
            )
        )
        ex._transports["file_read"] = mock_transport
        res = await ex._raw_execute("read_text_file", {})
        assert res.is_error
        assert registry.get_state("file_read") == McpServerHealthState.HEALTHY

    @pytest.mark.asyncio
    async def test_half_open_allows_trial_dispatch(self) -> None:
        """HALF_OPEN server allows trial dispatch; success restores HEALTHY."""
        import time as _time

        registry = McpServerHealthRegistry(
            failure_threshold=1, half_open_cooldown_sec=0.01
        )
        ex = _make_executor(configs={"file_read": _http_cfg()})
        ex.set_health_registry(registry)
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="ok", is_error=False, request_id="", server_key=""
            )
        )
        ex._transports["file_read"] = mock_transport
        registry.record_failure("file_read")
        assert registry.is_unavailable("file_read")
        _time.sleep(0.02)
        assert not registry.is_unavailable("file_read")
        assert registry.get_state("file_read") == McpServerHealthState.HALF_OPEN
        res = await ex._raw_execute("read_text_file", {})
        assert not res.is_error
        assert res.output == "ok"
        mock_transport.call.assert_called_once()
        assert registry.get_state("file_read") == McpServerHealthState.HEALTHY


class TestToolExecutorHealthTransitions:
    """End-to-end health-state transitions through ToolExecutor for specific error classes."""

    @pytest.mark.asyncio
    async def test_http_4xx_triggers_record_failure(self) -> None:
        """HTTP 4xx transport error triggers record_failure() at ToolExecutor level."""
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor(configs={"file_read": _http_cfg()})
        ex.set_health_registry(registry)
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            side_effect=TransportError("HTTPStatusError: 401 Unauthorized")
        )
        ex._transports["file_read"] = mock_transport
        res = await ex._raw_execute("read_text_file", {})

        assert res.is_error
        assert registry.get_state("file_read") == McpServerHealthState.DEGRADED
        assert "401" in res.output

    @pytest.mark.asyncio
    async def test_http_5xx_triggers_record_failure(self) -> None:
        """HTTP 5xx transport error triggers record_failure() at ToolExecutor level."""
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor(configs={"file_read": _http_cfg()})
        ex.set_health_registry(registry)
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            side_effect=TransportError("HTTPStatusError: 500 Internal Server Error")
        )
        ex._transports["file_read"] = mock_transport
        res = await ex._raw_execute("read_text_file", {})

        assert res.is_error
        assert registry.get_state("file_read") == McpServerHealthState.DEGRADED
        assert "500" in res.output

    @pytest.mark.asyncio
    async def test_timeout_triggers_record_failure(self) -> None:
        """Timeout transport error triggers record_failure() at ToolExecutor level."""
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor(configs={"file_read": _http_cfg()})
        ex.set_health_registry(registry)
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            side_effect=TransportError("timeout: request exceeded time limit")
        )
        ex._transports["file_read"] = mock_transport
        res = await ex._raw_execute("read_text_file", {})

        assert res.is_error
        assert registry.get_state("file_read") == McpServerHealthState.DEGRADED
        assert "timeout" in res.output.lower()

    @pytest.mark.asyncio
    async def test_connection_refused_triggers_record_failure(self) -> None:
        """Connection refused transport error triggers record_failure() at ToolExecutor level."""
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor(configs={"file_read": _http_cfg()})
        ex.set_health_registry(registry)
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            side_effect=TransportError("ConnectError: connection refused")
        )
        ex._transports["file_read"] = mock_transport
        res = await ex._raw_execute("read_text_file", {})

        assert res.is_error
        assert registry.get_state("file_read") == McpServerHealthState.DEGRADED
        assert "refused" in res.output.lower()

    @pytest.mark.asyncio
    async def test_malformed_response_triggers_record_failure(self) -> None:
        """Malformed response transport error triggers record_failure() at ToolExecutor level."""
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor(configs={"file_read": _http_cfg()})
        ex.set_health_registry(registry)
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            side_effect=TransportError("malformed response: expected dict, got str")
        )
        ex._transports["file_read"] = mock_transport
        res = await ex._raw_execute("read_text_file", {})

        assert res.is_error
        assert registry.get_state("file_read") == McpServerHealthState.DEGRADED

    @pytest.mark.asyncio
    async def test_tool_error_does_not_trigger_record_failure(self) -> None:
        """Tool-level error (HTTP 200 with is_error=True) calls record_success(), not record_failure()."""
        registry = McpServerHealthRegistry(failure_threshold=3)
        ex = _make_executor(configs={"file_read": _http_cfg()})
        ex.set_health_registry(registry)
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(
            return_value=ToolCallResult(
                output="tool error",
                is_error=True,
                request_id="req-1",
                server_key="file_read",
            )
        )
        ex._transports["file_read"] = mock_transport
        res = await ex._raw_execute("read_text_file", {})

        assert res.is_error
        # Tool-level error should NOT increment failure count — record_success() is called
        assert registry.get_state("file_read") == McpServerHealthState.HEALTHY


class TestCacheKeyFormat:
    def test_cache_key_is_plain_string_not_md5(self) -> None:
        """Cache key must use plain string format, not MD5 hex digest."""
        from shared.tool_executor import _json_dumps

        args: dict[str, Any] = {"path": "/tmp/f.txt"}
        key = f"read_text_file:{_json_dumps(args)}"
        assert key.startswith("read_text_file:")
        assert not re.fullmatch(r"[0-9a-f]{32}", key)

    def test_cache_key_identical_args_produce_identical_key(self) -> None:
        """Same tool + same args must always produce the same cache key."""
        from shared.tool_executor import _json_dumps

        args: dict[str, Any] = {"path": "/tmp/f.txt", "mode": "r"}
        key1 = f"read_text_file:{_json_dumps(args)}"
        key2 = f"read_text_file:{_json_dumps(args)}"
        assert key1 == key2

    def test_cache_key_different_tool_produces_different_key(self) -> None:
        """Different tool names must produce different cache keys for same args."""
        from shared.tool_executor import _json_dumps

        args: dict[str, Any] = {"path": "/tmp/f.txt"}
        key1 = f"read_text_file:{_json_dumps(args)}"
        key2 = f"write_file:{_json_dumps(args)}"
        assert key1 != key2

    def test_cache_key_different_args_produce_different_key(self) -> None:
        """Different args must produce different cache keys for same tool."""
        from shared.tool_executor import _json_dumps

        key1 = f"read_text_file:{_json_dumps({'path': '/tmp/a.txt'})}"
        key2 = f"read_text_file:{_json_dumps({'path': '/tmp/b.txt'})}"
        assert key1 != key2
