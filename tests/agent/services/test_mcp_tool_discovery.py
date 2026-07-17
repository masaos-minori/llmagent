"""
tests/agent/services/test_mcp_tool_discovery.py
Unit tests for agent.services.mcp_tool_discovery.McpToolDiscoveryService.

httpx.AsyncClient and AgentContext are mocked (mirrors tests/test_repl_health.py's
own mocking style).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from agent.services.mcp_tool_discovery import DiscoveryResult, McpToolDiscoveryService
from agent.shared.health_models import StartupCheckStatus
from shared.mcp_config import McpServerConfig, SecurityProfile, TransportType


def _async_result(value: object) -> AsyncMock:
    """Return an AsyncMock whose call returns the given value as a coroutine."""
    m = AsyncMock()
    m.return_value = value
    return m


def _resp(status_code: int = 200, json_value: object = None) -> MagicMock:
    """Build a MagicMock standing in for an httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_value
    return resp


def _server(url: str = "http://127.0.0.1:9000") -> McpServerConfig:
    return McpServerConfig(transport=TransportType.HTTP, url=url)


def _make_ctx(
    servers: dict[str, object],
    http: AsyncMock,
    security_profile: SecurityProfile = SecurityProfile.LOCAL,
) -> MagicMock:
    """Build a minimal mocked AgentContext (mirrors tests/test_repl_health.py's style)."""
    ctx = MagicMock()
    ctx.cfg.mcp.mcp_servers = servers
    ctx.cfg.mcp.security_profile = security_profile
    ctx.services_required.http = http
    return ctx


# ── discover_all() happy path ─────────────────────────────────────────────────


class TestDiscoverAllHappyPath:
    @pytest.mark.asyncio
    async def test_single_server_single_valid_tool_builds_registry(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "tools": [
                        {
                            "name": "grep",
                            "description": "search files",
                            "inputSchema": {"type": "object"},
                        }
                    ]
                },
            )
        )
        ctx = _make_ctx({"search_server": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert isinstance(result, DiscoveryResult)
        tool = result.registry.get("grep")
        assert tool.server_key == "search_server"
        assert tool.server_url == "http://127.0.0.1:9000"
        assert tool.description == "search files"
        assert tool.input_schema == {"type": "object"}
        assert tool.is_write is False
        assert tool.requires_serial is True  # safe default when is_write omitted
        assert result.findings == []
        assert result.unreachable == []

    @pytest.mark.asyncio
    async def test_explicit_is_write_true_defaults_requires_serial_false(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "tools": [
                        {
                            "name": "write_file",
                            "description": "writes a file",
                            "inputSchema": {},
                            "is_write": True,
                        }
                    ]
                },
            )
        )
        ctx = _make_ctx({"fs": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        tool = result.registry.get("write_file")
        assert tool.is_write is True
        assert tool.requires_serial is False


# ── per-entry schema validation ───────────────────────────────────────────────


class TestDiscoverAllMalformedEntries:
    @pytest.mark.asyncio
    async def test_missing_name_produces_warning_and_is_excluded(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(200, {"tools": [{"description": "d", "inputSchema": {}}]})
        )
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.registry.all_tools() == []
        assert len(result.findings) == 1
        assert result.findings[0].status == StartupCheckStatus.WARNING
        assert result.unreachable == []

    @pytest.mark.asyncio
    async def test_empty_string_name_produces_warning_and_is_excluded(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200, {"tools": [{"name": "   ", "description": "d", "inputSchema": {}}]}
            )
        )
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.registry.all_tools() == []
        assert len(result.findings) == 1
        assert result.findings[0].status == StartupCheckStatus.WARNING

    @pytest.mark.asyncio
    async def test_missing_description_produces_warning_and_is_excluded(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(200, {"tools": [{"name": "grep", "inputSchema": {}}]})
        )
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.registry.all_tools() == []
        assert len(result.findings) == 1
        assert result.findings[0].status == StartupCheckStatus.WARNING

    @pytest.mark.asyncio
    async def test_non_dict_input_schema_produces_warning_and_is_excluded(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "tools": [
                        {"name": "grep", "description": "d", "inputSchema": "nope"}
                    ]
                },
            )
        )
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.registry.all_tools() == []
        assert len(result.findings) == 1
        assert result.findings[0].status == StartupCheckStatus.WARNING

    @pytest.mark.asyncio
    async def test_non_dict_entry_itself_produces_warning_and_is_excluded(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(_resp(200, {"tools": ["not-a-dict"]}))
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.registry.all_tools() == []
        assert len(result.findings) == 1
        assert result.findings[0].status == StartupCheckStatus.WARNING

    @pytest.mark.asyncio
    async def test_malformed_entry_does_not_exclude_other_valid_entries(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "tools": [
                        {"description": "no name", "inputSchema": {}},
                        {"name": "grep", "description": "d", "inputSchema": {}},
                    ]
                },
            )
        )
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.registry.get("grep").server_key == "srv"
        assert len(result.findings) == 1
        assert result.findings[0].status == StartupCheckStatus.WARNING


# ── whole-server unreachable/malformed responses ──────────────────────────────


class TestDiscoverAllUnreachableServers:
    @pytest.mark.asyncio
    async def test_non_200_status_marks_server_unreachable(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(_resp(503, {}))
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.unreachable == ["srv"]
        assert len(result.findings) == 1
        assert result.findings[0].status == StartupCheckStatus.WARNING
        assert result.registry.all_tools() == []

    @pytest.mark.asyncio
    async def test_invalid_json_body_marks_server_unreachable(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        resp = MagicMock()
        resp.status_code = 200
        resp.json.side_effect = ValueError("bad json")
        http.get = _async_result(resp)
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.unreachable == ["srv"]
        assert len(result.findings) == 1
        assert result.findings[0].status == StartupCheckStatus.WARNING

    @pytest.mark.asyncio
    async def test_non_dict_top_level_body_marks_server_unreachable(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(_resp(200, ["not", "a", "dict"]))
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.unreachable == ["srv"]
        assert len(result.findings) == 1

    @pytest.mark.asyncio
    async def test_tools_field_missing_marks_server_unreachable(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(_resp(200, {"status": "ok"}))
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.unreachable == ["srv"]
        assert len(result.findings) == 1

    @pytest.mark.asyncio
    async def test_tools_field_not_a_list_marks_server_unreachable(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(_resp(200, {"tools": "not-a-list"}))
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.unreachable == ["srv"]
        assert len(result.findings) == 1

    @pytest.mark.asyncio
    async def test_connect_error_marks_server_unreachable(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.unreachable == ["srv"]
        assert len(result.findings) == 1
        assert "refused" in result.findings[0].message

    @pytest.mark.asyncio
    async def test_os_error_marks_server_unreachable(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock(side_effect=OSError("network down"))
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.unreachable == ["srv"]
        assert len(result.findings) == 1

    @pytest.mark.asyncio
    async def test_one_unreachable_server_others_still_processed(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)

        async def _get(url: str, timeout: float = 5.0) -> MagicMock:
            if "bad" in url:
                raise httpx.ConnectError("refused")
            return _resp(
                200,
                {"tools": [{"name": "grep", "description": "d", "inputSchema": {}}]},
            )

        http.get = AsyncMock(side_effect=_get)
        ctx = _make_ctx(
            {
                "bad_server": _server("http://bad-host:9000"),
                "good_server": _server("http://good-host:9000"),
            },
            http,
        )

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.unreachable == ["bad_server"]
        assert result.registry.get("grep").server_key == "good_server"


# ── cross-server duplicate tool names ──────────────────────────────────────────


class TestDiscoverAllDuplicates:
    def _dup_ctx(self, security_profile: SecurityProfile) -> MagicMock:
        http = AsyncMock(spec=httpx.AsyncClient)

        async def _get(url: str, timeout: float = 5.0) -> MagicMock:
            return _resp(
                200,
                {"tools": [{"name": "grep", "description": "d", "inputSchema": {}}]},
            )

        http.get = AsyncMock(side_effect=_get)
        return _make_ctx(
            {
                "server_a": _server("http://a:9000"),
                "server_b": _server("http://b:9000"),
            },
            http,
            security_profile=security_profile,
        )

    @pytest.mark.asyncio
    async def test_duplicate_name_production_is_fatal_and_excluded(self) -> None:
        ctx = self._dup_ctx(SecurityProfile.PRODUCTION)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.registry.all_tools() == []
        assert len(result.findings) == 1
        assert result.findings[0].status == StartupCheckStatus.FATAL
        assert "grep" in result.findings[0].message

    @pytest.mark.asyncio
    async def test_duplicate_name_local_is_warning_and_still_excluded(self) -> None:
        ctx = self._dup_ctx(SecurityProfile.LOCAL)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.registry.all_tools() == []
        assert len(result.findings) == 1
        assert result.findings[0].status == StartupCheckStatus.WARNING
        assert "grep" in result.findings[0].message


# ── non-HTTP / empty-URL server filtering ──────────────────────────────────────


class TestDiscoverAllServerFilter:
    @pytest.mark.asyncio
    async def test_empty_url_server_is_skipped(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock()
        cfg = MagicMock()
        cfg.transport = TransportType.HTTP
        cfg.url = ""
        ctx = _make_ctx({"empty_url_server": cfg}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        http.get.assert_not_called()
        assert result.registry.all_tools() == []
        assert result.findings == []
        assert result.unreachable == []

    @pytest.mark.asyncio
    async def test_non_http_transport_server_is_skipped(self) -> None:
        # TransportType currently defines only HTTP; a stub config value stands
        # in for a hypothetical non-HTTP transport to exercise the filter branch.
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock()
        cfg = MagicMock()
        cfg.transport = "stdio"
        cfg.url = "http://127.0.0.1:9000"
        ctx = _make_ctx({"stdio_server": cfg}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        http.get.assert_not_called()
        assert result.registry.all_tools() == []
