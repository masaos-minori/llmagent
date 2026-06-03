"""tests/test_tool_executor_routing.py
Unit tests for ToolExecutor: resolver integration, lifecycle injection,
set_lifecycle(), transport-dispatch paths, and auth header injection.
"""

from __future__ import annotations

from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import shared.plugin_registry as plugin_registry
from shared.mcp_config import McpServerConfig
from shared.tool_executor import (
    HttpTransport,
    LifecycleProtocol,
    StdioTransport,
    ToolExecutor,
)


def _http_cfg(url: str = "http://127.0.0.1:8000") -> McpServerConfig:
    return McpServerConfig("http", url, [], "")


def _stdio_cfg() -> McpServerConfig:
    return McpServerConfig("stdio", "", ["python", "s.py"], "")


def _make_executor(
    configs: dict[str, McpServerConfig] | None = None,
    concurrency_limits: dict[str, int] | None = None,
) -> ToolExecutor:
    http = MagicMock(spec=httpx.AsyncClient)
    return ToolExecutor(
        http,
        cache_ttl=60.0,
        server_configs=configs or {"file_read": _http_cfg()},
        concurrency_limits=concurrency_limits,
    )


class TestResolverIntegration:
    def test_resolver_resolves_static_fallback(self) -> None:
        ex = _make_executor({"file_read": _http_cfg()})
        assert ex._resolver.resolve("read_text_file") == "file_read"

    def test_resolver_raises_for_unknown_tool(self) -> None:
        ex = _make_executor()
        with pytest.raises(ValueError, match="Unknown tool"):
            ex._resolver.resolve("no_such_tool")

    def test_concurrency_limits_unknown_key_warns(self, caplog: Any) -> None:
        import logging

        with caplog.at_level(logging.WARNING, logger="shared.tool_executor"):
            _make_executor(
                configs={"file_read": _http_cfg()},
                concurrency_limits={"totally_unknown": 2},
            )
        assert "unknown server key" in caplog.text.lower()

    def test_concurrency_limits_known_key_no_warning(self, caplog: Any) -> None:
        import logging

        with caplog.at_level(logging.WARNING, logger="shared.tool_executor"):
            _make_executor(
                configs={"file_read": _http_cfg()},
                concurrency_limits={"file_read": 2},
            )
        assert "unknown server key" not in caplog.text.lower()


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

        call_order: list[str] = []

        mock_lc = AsyncMock(spec=LifecycleProtocol)

        async def fake_ensure(key: str) -> None:
            call_order.append(f"ensure:{key}")

        mock_lc.ensure_ready = fake_ensure
        ex.set_lifecycle(mock_lc)

        # Patch the transport to record call order
        mock_transport = AsyncMock()

        def _record_and_ok(*a: object, **kw: object) -> tuple[str, bool, str]:
            call_order.append("call")
            return ("ok", False, "")

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
        assert ex._lifecycle is None

        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(return_value=("result", False, ""))
        ex._transports["file_read"] = mock_transport

        result, is_err, _ = await ex._raw_execute("read_text_file", {})
        assert not is_err

    @pytest.mark.asyncio
    async def test_no_transport_returns_error(self) -> None:
        http = MagicMock(spec=httpx.AsyncClient)
        configs = {"shell": _stdio_cfg()}
        ex = ToolExecutor(http, cache_ttl=60.0, server_configs=configs)
        # stdio transport starts as None (not yet started)
        result, is_err, _ = await ex._raw_execute("shell_run", {})
        assert is_err
        assert "not started" in result or "No transport" in result


class TestHttpTransportAuthHeader:
    @pytest.mark.asyncio
    async def test_auth_token_set_sends_bearer_header(self) -> None:
        cfg = McpServerConfig(
            "http", "http://127.0.0.1:8000", [], "", auth_token="my-token"
        )
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"result": "ok", "is_error": False}
        mock_resp.raise_for_status = MagicMock()
        mock_resp.headers = {}
        mock_http.post = AsyncMock(return_value=mock_resp)

        transport = HttpTransport(mock_http, "http://127.0.0.1:8000", "svc", cfg)
        await transport.call("my_tool", {})

        call_kwargs = mock_http.post.call_args.kwargs
        assert call_kwargs["headers"] == {"Authorization": "Bearer my-token"}

    @pytest.mark.asyncio
    async def test_no_auth_token_sends_empty_headers(self) -> None:
        cfg = McpServerConfig("http", "http://127.0.0.1:8000", [], "", auth_token="")
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"result": "ok", "is_error": False}
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
        mock_resp.json.return_value = {"result": "ok", "is_error": False}
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
        mock_resp.json.return_value = {"result": "ok", "is_error": False}
        mock_resp.raise_for_status = MagicMock()
        mock_resp.headers = {"x-request-id": "abc-123"}
        mock_http.post = AsyncMock(return_value=mock_resp)

        transport = HttpTransport(mock_http, "http://127.0.0.1:8000", "svc")
        _result, _is_err, x_req_id = await transport.call("my_tool", {})

        assert x_req_id == "abc-123"

    @pytest.mark.asyncio
    async def test_x_request_id_empty_when_header_absent(self) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"result": "ok", "is_error": False}
        mock_resp.raise_for_status = MagicMock()
        mock_resp.headers = {}
        mock_http.post = AsyncMock(return_value=mock_resp)

        transport = HttpTransport(mock_http, "http://127.0.0.1:8000", "svc")
        _result, _is_err, x_req_id = await transport.call("my_tool", {})

        assert x_req_id == ""


class TestHttpTransportErrors:
    @pytest.mark.asyncio
    async def test_http_status_error_returns_error_tuple(self) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        req = httpx.Request("POST", "http://127.0.0.1:8000/v1/call_tool")
        resp_obj = httpx.Response(500, request=req)
        mock_http.post = AsyncMock(
            side_effect=httpx.HTTPStatusError(
                "server error", request=req, response=resp_obj
            )
        )
        transport = HttpTransport(mock_http, "http://127.0.0.1:8000", "svc")
        result, is_err, x_req_id = await transport.call("my_tool", {})
        assert is_err
        assert "HTTPStatusError" in result
        assert x_req_id == ""

    @pytest.mark.asyncio
    async def test_request_error_returns_error_tuple(self) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        req = httpx.Request("POST", "http://127.0.0.1:8000/v1/call_tool")
        mock_http.post = AsyncMock(
            side_effect=httpx.ConnectError("refused", request=req)
        )
        transport = HttpTransport(mock_http, "http://127.0.0.1:8000", "svc")
        result, is_err, x_req_id = await transport.call("my_tool", {})
        assert is_err
        assert x_req_id == ""

    @pytest.mark.asyncio
    async def test_generic_exception_returns_error_tuple(self) -> None:
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_http.post = AsyncMock(side_effect=RuntimeError("unexpected"))
        transport = HttpTransport(mock_http, "http://127.0.0.1:8000", "svc")
        result, is_err, x_req_id = await transport.call("my_tool", {})
        assert is_err
        assert "RuntimeError" in result
        assert x_req_id == ""


class TestStdioTransportCall:
    @pytest.mark.asyncio
    async def test_not_alive_returns_error(self) -> None:
        transport = StdioTransport(["python", "s.py"], "key")
        result, is_err, x_req_id = await transport.call("my_tool", {})
        assert is_err
        assert "not running" in result
        assert x_req_id == ""

    @pytest.mark.asyncio
    async def test_success_response_returns_result(self) -> None:
        transport = StdioTransport(["python", "s.py"], "key")
        mock_proc = MagicMock()
        mock_proc.returncode = None
        mock_proc.stdin = MagicMock()
        mock_proc.stdin.drain = AsyncMock()
        mock_proc.stdout = MagicMock()
        mock_proc.stdout.readline = AsyncMock(
            return_value=b'{"result": "ok", "is_error": false}\n'
        )
        transport._proc = mock_proc
        result, is_err, x_req_id = await transport.call("my_tool", {})
        assert not is_err
        assert result == "ok"
        assert x_req_id == ""

    @pytest.mark.asyncio
    async def test_invalid_json_returns_error(self) -> None:
        transport = StdioTransport(["python", "s.py"], "key")
        mock_proc = MagicMock()
        mock_proc.returncode = None
        mock_proc.stdin = MagicMock()
        mock_proc.stdin.drain = AsyncMock()
        mock_proc.stdout = MagicMock()
        mock_proc.stdout.readline = AsyncMock(return_value=b"not-json\n")
        transport._proc = mock_proc
        result, is_err, x_req_id = await transport.call("my_tool", {})
        assert is_err
        assert x_req_id == ""

    @pytest.mark.asyncio
    async def test_timeout_returns_error(self) -> None:
        transport = StdioTransport(["python", "s.py"], "key")
        mock_proc = MagicMock()
        mock_proc.returncode = None
        mock_proc.stdin = MagicMock()
        mock_proc.stdin.drain = AsyncMock()
        mock_proc.stdout = MagicMock()
        transport._proc = mock_proc
        with patch("asyncio.wait_for", new=AsyncMock(side_effect=TimeoutError())):
            result, is_err, x_req_id = await transport.call("my_tool", {})
        assert is_err
        assert "timeout" in result
        assert x_req_id == ""

    @pytest.mark.asyncio
    async def test_transport_exception_returns_error(self) -> None:
        transport = StdioTransport(["python", "s.py"], "key")
        mock_proc = MagicMock()
        mock_proc.returncode = None
        mock_proc.stdin = MagicMock()
        mock_proc.stdin.drain = AsyncMock(side_effect=OSError("pipe broken"))
        mock_proc.stdout = MagicMock()
        transport._proc = mock_proc
        result, is_err, x_req_id = await transport.call("my_tool", {})
        assert is_err
        assert x_req_id == ""


class TestToolExecutorExecute:
    @pytest.mark.asyncio
    async def test_plugin_tool_success_returns_empty_x_request_id(self) -> None:
        plugin_registry._reset_for_testing()

        @plugin_registry.register_tool("plugin_ok_tool")
        async def _handler(args: dict) -> tuple[str, bool]:
            return "plugin result", False

        ex = _make_executor()
        result, is_err, x_req = await ex.execute("plugin_ok_tool", {})
        assert result == "plugin result"
        assert not is_err
        assert x_req == ""
        plugin_registry._reset_for_testing()

    @pytest.mark.asyncio
    async def test_plugin_tool_error_returns_empty_x_request_id(self) -> None:
        plugin_registry._reset_for_testing()

        @plugin_registry.register_tool("plugin_bad_tool")
        async def _bad_handler(args: dict) -> tuple[str, bool]:
            raise RuntimeError("boom")

        ex = _make_executor()
        result, is_err, x_req = await ex.execute("plugin_bad_tool", {})
        assert is_err
        assert "[plugin error]" in result
        assert x_req == ""
        plugin_registry._reset_for_testing()

    @pytest.mark.asyncio
    async def test_cache_hit_returns_empty_x_request_id(self) -> None:
        ex = _make_executor()
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(return_value=("cached result", False, "req-1"))
        ex._transports["file_read"] = mock_transport

        await ex.execute("read_text_file", {"path": "f"})
        result, is_err, x_req = await ex.execute("read_text_file", {"path": "f"})
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
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(return_value=("result", False, "req-1"))
        ex._transports["file_read"] = mock_transport

        await ex.execute("read_text_file", {"path": "f"})
        result, is_err, x_req = await ex.execute("read_text_file", {"path": "f"})
        assert result == "result"
        assert mock_transport.call.call_count == 2

    @pytest.mark.asyncio
    async def test_execute_propagates_x_request_id_on_cache_miss(self) -> None:
        ex = _make_executor()
        mock_transport = AsyncMock()
        mock_transport.call = AsyncMock(return_value=("ok", False, "req-xyz"))
        ex._transports["file_read"] = mock_transport

        _result, _is_err, x_req = await ex.execute("read_text_file", {"path": "f"})
        assert x_req == "req-xyz"


class TestStdioTransportStart:
    @pytest.mark.asyncio
    async def test_start_passes_working_dir_to_subprocess(self, tmp_path: Any) -> None:
        transport = StdioTransport(["python", "s.py"], "key", working_dir=str(tmp_path))
        mock_proc = MagicMock()
        mock_proc.pid = 1
        mock_proc.returncode = None
        with patch(
            "asyncio.create_subprocess_exec", new=AsyncMock(return_value=mock_proc)
        ) as mock_exec:
            await transport.start()
        _, kwargs = mock_exec.call_args
        assert kwargs["cwd"] == str(tmp_path)

    @pytest.mark.asyncio
    async def test_start_passes_env_merged_to_subprocess(
        self, tmp_path: Any, monkeypatch: Any
    ) -> None:
        monkeypatch.setenv("EXISTING_VAR", "existing_value")
        transport = StdioTransport(
            ["python", "s.py"],
            "key",
            working_dir=str(tmp_path),
            env={"EXTRA_VAR": "extra_value"},
        )
        mock_proc = MagicMock()
        mock_proc.pid = 1
        mock_proc.returncode = None
        with patch(
            "asyncio.create_subprocess_exec", new=AsyncMock(return_value=mock_proc)
        ) as mock_exec:
            await transport.start()
        _, kwargs = mock_exec.call_args
        merged = kwargs["env"]
        assert merged is not None
        assert merged["EXISTING_VAR"] == "existing_value"
        assert merged["EXTRA_VAR"] == "extra_value"

    @pytest.mark.asyncio
    async def test_start_empty_working_dir_passes_none_cwd(self) -> None:
        transport = StdioTransport(["python", "s.py"], "key", working_dir="")
        mock_proc = MagicMock()
        mock_proc.pid = 1
        mock_proc.returncode = None
        with patch(
            "asyncio.create_subprocess_exec", new=AsyncMock(return_value=mock_proc)
        ) as mock_exec:
            await transport.start()
        _, kwargs = mock_exec.call_args
        assert kwargs["cwd"] is None

    @pytest.mark.asyncio
    async def test_start_nonexistent_working_dir_raises(self) -> None:
        transport = StdioTransport(
            ["python", "s.py"], "key", working_dir="/nonexistent/path/xyz"
        )
        with pytest.raises(ValueError, match="does not exist"):
            await transport.start()


class TestSetSessionId:
    @pytest.mark.asyncio
    async def test_session_id_injected_into_http_transport_header(self) -> None:
        """set_session_id() propagates X-Session-Id to all HttpTransport instances."""
        cfg = McpServerConfig("http", "http://127.0.0.1:8000", [], "")
        mock_http = AsyncMock(spec=httpx.AsyncClient)
        mock_resp = MagicMock()
        mock_resp.json.return_value = {"result": "ok", "is_error": False}
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
        cfg = McpServerConfig("http", "http://127.0.0.1:8000", [], "")
        mock_http = MagicMock(spec=httpx.AsyncClient)
        ex = ToolExecutor(mock_http, cache_ttl=60.0, server_configs={"srv": cfg})
        ex.set_session_id("")

        transport = ex._transports["srv"]
        assert isinstance(transport, HttpTransport)
        assert transport._session_id == ""

    def test_set_session_id_skips_stdio_transports(self) -> None:
        """set_session_id() must not raise for servers with no HttpTransport."""
        cfg = McpServerConfig("stdio", "", ["python", "s.py"], "")
        mock_http = MagicMock(spec=httpx.AsyncClient)
        ex = ToolExecutor(mock_http, cache_ttl=60.0, server_configs={"stdio_srv": cfg})
        # Must not raise even though the transport is not an HttpTransport
        ex.set_session_id("sess-xyz")


# ── apply_config ──────────────────────────────────────────────────────────────


class TestToolExecutorApplyConfig:
    def _make_executor(self) -> ToolExecutor:
        from unittest.mock import AsyncMock

        import httpx
        from shared.mcp_config import McpServerConfig
        from shared.tool_executor import ToolExecutor

        cfg = McpServerConfig("http", "http://localhost:8005", [], "svc")
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
