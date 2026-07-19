"""
tests/agent/services/test_mcp_tool_discovery.py
Unit tests for agent.services.mcp_tool_discovery.McpToolDiscoveryService.

httpx.AsyncClient and AgentContext are mocked (mirrors tests/test_repl_health.py's
own mocking style).

Also includes real-app schema validation tests against each MCP server's
/v1/tools endpoint (TestToolsEndpointSchemaVersion, TestToolsEndpointToolShape).
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from agent.services.mcp_tool_discovery import DiscoveryResult, McpToolDiscoveryService
from agent.shared.health_models import HealthCheckResult, StartupCheckStatus
from fastapi.testclient import TestClient
from shared.mcp_config import McpServerConfig, SecurityProfile, TransportType
from shared.tool_registry import ToolDefinition, get_registry

_IN_SCOPE_SERVERS = [
    ("mcp_servers.mdq.server", "app", "mdq"),
    ("mcp_servers.cicd.server", "app", "cicd"),
    ("mcp_servers.github.server", "app", "github"),
    ("mcp_servers.git.server", "app", "git"),
    ("mcp_servers.web_search.server", "app", "web_search"),
    ("mcp_servers.shell.server", "app", "shell"),
    ("mcp_servers.file.read_server", "app", "file_read"),
    ("mcp_servers.file.write_server", "app", "file_write"),
    ("mcp_servers.file.delete_server", "app", "file_delete"),
]


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
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 0
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
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1
        assert any(f.status == StartupCheckStatus.WARNING for f in mcp_findings)
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
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1
        assert any(f.status == StartupCheckStatus.WARNING for f in mcp_findings)

    @pytest.mark.asyncio
    async def test_missing_description_produces_warning_and_is_excluded(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(200, {"tools": [{"name": "grep", "inputSchema": {}}]})
        )
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.registry.all_tools() == []
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1
        assert any(f.status == StartupCheckStatus.WARNING for f in mcp_findings)

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
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1
        assert any(f.status == StartupCheckStatus.WARNING for f in mcp_findings)

    @pytest.mark.asyncio
    async def test_non_dict_entry_itself_produces_warning_and_is_excluded(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(_resp(200, {"tools": ["not-a-dict"]}))
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.registry.all_tools() == []
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1
        assert any(f.status == StartupCheckStatus.WARNING for f in mcp_findings)

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
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1
        assert any(f.status == StartupCheckStatus.WARNING for f in mcp_findings)


# ── whole-server unreachable/malformed responses ──────────────────────────────


class TestDiscoverAllUnreachableServers:
    @pytest.mark.asyncio
    async def test_non_200_status_marks_server_unreachable(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(_resp(503, {}))
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.unreachable == ["srv"]
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1
        assert any(f.status == StartupCheckStatus.WARNING for f in mcp_findings)
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
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1
        assert any(f.status == StartupCheckStatus.WARNING for f in mcp_findings)

    @pytest.mark.asyncio
    async def test_non_dict_top_level_body_marks_server_unreachable(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(_resp(200, ["not", "a", "dict"]))
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.unreachable == ["srv"]
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1

    @pytest.mark.asyncio
    async def test_tools_field_missing_marks_server_unreachable(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(_resp(200, {"status": "ok"}))
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.unreachable == ["srv"]
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1

    @pytest.mark.asyncio
    async def test_tools_field_not_a_list_marks_server_unreachable(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(_resp(200, {"tools": "not-a-list"}))
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.unreachable == ["srv"]
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1

    @pytest.mark.asyncio
    async def test_connect_error_marks_server_unreachable(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.unreachable == ["srv"]
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1
        assert any("refused" in f.message for f in mcp_findings)

    @pytest.mark.asyncio
    async def test_os_error_marks_server_unreachable(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock(side_effect=OSError("network down"))
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.unreachable == ["srv"]
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1

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
        ctx = _make_ctx(
            {
                "server_a": _server("http://a:9000"),
                "server_b": _server("http://b:9000"),
            },
            http,
            security_profile=security_profile,
        )
        ctx.cfg.tool.tool_definitions_strict = False
        return ctx

    @pytest.mark.asyncio
    async def test_duplicate_name_production_is_fatal_and_excluded(self) -> None:
        ctx = self._dup_ctx(SecurityProfile.PRODUCTION)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.registry.all_tools() == []
        dup_findings = [f for f in result.findings if "duplicate" in f.message]
        assert len(dup_findings) == 1
        assert dup_findings[0].status == StartupCheckStatus.FATAL

    @pytest.mark.asyncio
    async def test_duplicate_name_local_is_warning_and_still_excluded(self) -> None:
        ctx = self._dup_ctx(SecurityProfile.LOCAL)

        result = await McpToolDiscoveryService(ctx).discover_all()

        assert result.registry.all_tools() == []
        dup_findings = [f for f in result.findings if "duplicate" in f.message]
        assert len(dup_findings) == 1
        assert dup_findings[0].status == StartupCheckStatus.WARNING


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


# ── real-app schema validation matrix ──────────────────────────────────────────


class TestToolsEndpointSchemaVersion:
    @pytest.mark.parametrize("import_path, app_attr, server_key", _IN_SCOPE_SERVERS)
    def test_schema_version_present(
        self, import_path: str, app_attr: str, server_key: str
    ) -> None:
        import importlib

        from mcp_servers.server import MCP_TOOL_SCHEMA_VERSION

        module = importlib.import_module(import_path)
        client = TestClient(getattr(module, app_attr), raise_server_exceptions=True)
        body = client.get("/v1/tools").json()
        assert "schema_version" in body, (
            f"[{server_key}] /v1/tools response missing schema_version"
        )
        assert body["schema_version"] == MCP_TOOL_SCHEMA_VERSION, (
            f"[{server_key}] schema_version mismatch: got {body['schema_version']!r}, "
            f"expected {MCP_TOOL_SCHEMA_VERSION!r}"
        )


class TestToolsEndpointToolShape:
    @pytest.mark.parametrize("import_path, app_attr, server_key", _IN_SCOPE_SERVERS)
    def test_every_tool_matches_schema(
        self, import_path: str, app_attr: str, server_key: str
    ) -> None:
        import importlib

        module = importlib.import_module(import_path)
        client = TestClient(getattr(module, app_attr), raise_server_exceptions=True)
        body = client.get("/v1/tools").json()
        for tool in body.get("tools", []):
            name = tool.get("name")
            assert name, f"[{server_key}] tool {tool!r}: missing/empty name"
            desc = tool.get("description")
            assert desc, f"[{server_key}] tool {name!r}: missing description"
            input_schema = tool.get("inputSchema")
            assert isinstance(input_schema, dict), (
                f"[{server_key}] tool {name!r}: inputSchema not object"
            )
            if "status" in tool:
                assert isinstance(tool["status"], str), (
                    f"[{server_key}] tool {name!r}: status not string"
                )
            if "is_write" in tool:
                assert isinstance(tool["is_write"], bool), (
                    f"[{server_key}] tool {name!r}: is_write not bool"
                )
            if "requires_serial" in tool:
                assert isinstance(tool["requires_serial"], bool), (
                    f"[{server_key}] tool {name!r}: requires_serial not bool"
                )
            if "resource_scope" in tool:
                assert isinstance(tool["resource_scope"], str), (
                    f"[{server_key}] tool {name!r}: resource_scope not string"
                )


@pytest.mark.asyncio
async def test_resource_scope_type_checked_when_present_synthetic() -> None:
    http = AsyncMock(spec=httpx.AsyncClient)
    http.get = _async_result(
        _resp(
            200,
            {
                "tools": [
                    {
                        "name": "test_tool",
                        "description": "desc",
                        "inputSchema": {},
                        "resource_scope": 123,
                    }
                ]
            },
        )
    )
    ctx = _make_ctx({"srv": _server()}, http)

    result = await McpToolDiscoveryService(ctx).discover_all()

    assert result.registry.all_tools() == []
    resource_scope_findings = [
        f
        for f in result.findings
        if "resource_scope" in f.message and "test_tool" in f.message
    ]
    assert len(resource_scope_findings) == 1
    assert resource_scope_findings[0].status == StartupCheckStatus.WARNING

    http2 = AsyncMock(spec=httpx.AsyncClient)
    http2.get = _async_result(
        _resp(
            200,
            {
                "tools": [
                    {
                        "name": "test_tool_ok",
                        "description": "desc",
                        "inputSchema": {},
                        "resource_scope": "filesystem",
                    }
                ]
            },
        )
    )
    ctx2 = _make_ctx({"srv": _server()}, http2)

    result2 = await McpToolDiscoveryService(ctx2).discover_all()

    assert result2.registry.get("test_tool_ok") is not None
    assert not any("resource_scope" in f.message for f in result2.findings)


@pytest.mark.asyncio
async def test_missing_schema_version_tolerated() -> None:
    http = AsyncMock(spec=httpx.AsyncClient)
    http.get = _async_result(
        _resp(
            200,
            {
                "tools": [
                    {
                        "name": "legacy_tool",
                        "description": "legacy",
                        "inputSchema": {},
                    }
                ]
            },
        )
    )
    ctx = _make_ctx({"legacy_srv": _server()}, http)

    result = await McpToolDiscoveryService(ctx).discover_all()

    assert result.registry.get("legacy_tool") is not None
    assert not any("schema_version" in f.message for f in result.findings)


@pytest.mark.asyncio
async def test_missing_capabilities_tolerated() -> None:
    http = AsyncMock(spec=httpx.AsyncClient)
    http.get = _async_result(
        _resp(
            200,
            {
                "tools": [
                    {
                        "name": "read_file",
                        "description": "reads a file",
                        "inputSchema": {"type": "object"},
                    }
                ]
            },
        )
    )
    ctx = _make_ctx({"fs": _server()}, http)

    result = await McpToolDiscoveryService(ctx).discover_all()

    tool = result.registry.get("read_file")
    assert tool is not None
    assert tool.capabilities == ()
    assert not any("capabilities" in f.message for f in result.findings)


@pytest.mark.asyncio
async def test_capabilities_present_and_valid_normalizes_to_tuple() -> None:
    http = AsyncMock(spec=httpx.AsyncClient)
    http.get = _async_result(
        _resp(
            200,
            {
                "tools": [
                    {
                        "name": "delete_file",
                        "description": "deletes a file",
                        "inputSchema": {"type": "object"},
                        "capabilities": ["filesystem.read", "filesystem.write"],
                    }
                ]
            },
        )
    )
    ctx = _make_ctx({"fs": _server()}, http)

    result = await McpToolDiscoveryService(ctx).discover_all()

    tool = result.registry.get("delete_file")
    assert tool is not None
    assert tool.capabilities == ("filesystem.read", "filesystem.write")


@pytest.mark.asyncio
async def test_malformed_capabilities_produces_warning_not_fatal() -> None:
    http = AsyncMock(spec=httpx.AsyncClient)
    http.get = _async_result(
        _resp(
            200,
            {
                "tools": [
                    {
                        "name": "bad_tool",
                        "description": "malformed capabilities",
                        "inputSchema": {"type": "object"},
                        "capabilities": "filesystem.read",
                    }
                ]
            },
        )
    )
    ctx = _make_ctx({"fs": _server()}, http)

    result = await McpToolDiscoveryService(ctx).discover_all()

    assert result.registry.all_tools() == []
    capability_findings = [f for f in result.findings if "capabilities" in f.message]
    assert len(capability_findings) == 1
    assert capability_findings[0].status == StartupCheckStatus.WARNING
    assert "bad_tool" in capability_findings[0].message


# ── drift-vs-registry detection ────────────────────────────────────────────────


class TestDriftDetection:
    @pytest.mark.asyncio
    async def test_duplicate_live_tool_warns_when_local(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)

        async def _get(url: str, timeout: float = 5.0) -> MagicMock:
            return _resp(
                200,
                {"tools": [{"name": "tool_a", "description": "d", "inputSchema": {}}]},
            )

        http.get = AsyncMock(side_effect=_get)
        ctx = _make_ctx(
            {
                "srv1": _server("http://srv1:9000"),
                "srv2": _server("http://srv2:9000"),
            },
            http,
            security_profile=SecurityProfile.LOCAL,
        )
        ctx.cfg.tool.tool_definitions_strict = False

        result = await McpToolDiscoveryService(ctx).discover_all()

        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        dup_findings = [f for f in mcp_findings if "duplicate" in f.message.lower()]
        assert len(dup_findings) == 1
        assert dup_findings[0].status == StartupCheckStatus.WARNING
        assert "tool_a" in dup_findings[0].message
        # duplicate tool should NOT be in the registry
        assert not any(t.name == "tool_a" for t in result.registry.all_tools())

    @pytest.mark.asyncio
    async def test_duplicate_live_tool_fatal_when_production(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)

        async def _get(url: str, timeout: float = 5.0) -> MagicMock:
            return _resp(
                200,
                {"tools": [{"name": "tool_a", "description": "d", "inputSchema": {}}]},
            )

        http.get = AsyncMock(side_effect=_get)
        ctx = _make_ctx(
            {
                "srv1": _server("http://srv1:9000"),
                "srv2": _server("http://srv2:9000"),
            },
            http,
            security_profile=SecurityProfile.PRODUCTION,
        )
        ctx.cfg.tool.tool_definitions_strict = False

        result = await McpToolDiscoveryService(ctx).discover_all()

        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        dup_findings = [f for f in mcp_findings if "duplicate" in f.message.lower()]
        assert len(dup_findings) == 1
        assert dup_findings[0].status == StartupCheckStatus.FATAL

    @pytest.mark.asyncio
    async def test_duplicate_live_tool_fatal_when_strict_even_if_local(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)

        async def _get(url: str, timeout: float = 5.0) -> MagicMock:
            return _resp(
                200,
                {"tools": [{"name": "tool_a", "description": "d", "inputSchema": {}}]},
            )

        http.get = AsyncMock(side_effect=_get)
        ctx = _make_ctx(
            {
                "srv1": _server("http://srv1:9000"),
                "srv2": _server("http://srv2:9000"),
            },
            http,
            security_profile=SecurityProfile.LOCAL,
        )
        ctx.cfg.tool.tool_definitions_strict = True

        result = await McpToolDiscoveryService(ctx).discover_all()

        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        dup_findings = [f for f in mcp_findings if "duplicate" in f.message.lower()]
        assert len(dup_findings) == 1
        assert dup_findings[0].status == StartupCheckStatus.FATAL

    @pytest.mark.asyncio
    async def test_no_duplicate_no_drift_finding(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery._check_tool_definitions",
            AsyncMock(return_value=HealthCheckResult()),
        )

        # Register both tools in the static registry so live discovery matches
        reg = get_registry()
        reg.register(ToolDefinition(name="tool_a", server_key="srv1"))
        reg.register(ToolDefinition(name="tool_b", server_key="srv2"))

        try:
            http = AsyncMock(spec=httpx.AsyncClient)

            async def _get(url: str, timeout: float = 5.0) -> MagicMock:
                if "srv1" in url:
                    return _resp(
                        200,
                        {
                            "tools": [
                                {
                                    "name": "tool_a",
                                    "description": "d",
                                    "inputSchema": {},
                                }
                            ]
                        },
                    )
                return _resp(
                    200,
                    {
                        "tools": [
                            {"name": "tool_b", "description": "d", "inputSchema": {}}
                        ]
                    },
                )

            http.get = AsyncMock(side_effect=_get)
            ctx = _make_ctx(
                {
                    "srv1": _server("http://srv1:9000"),
                    "srv2": _server("http://srv2:9000"),
                },
                http,
                security_profile=SecurityProfile.LOCAL,
            )
            ctx.cfg.tool.tool_definitions_strict = False

            result = await McpToolDiscoveryService(ctx).discover_all()

            mcp_findings = [
                f for f in result.findings if f.source == "mcp_tool_discovery"
            ]
            assert not any("drift" in f.message.lower() for f in mcp_findings)
        finally:
            reg._tools.pop("tool_a", None)
            reg._tools.pop("tool_b", None)
            if "srv1" in reg._by_server:
                reg._by_server["srv1"].remove("tool_a")
            if "srv2" in reg._by_server:
                reg._by_server["srv2"].remove("tool_b")

    @pytest.mark.asyncio
    async def test_drift_vs_registry_mismatch_warns(self) -> None:
        from shared.tool_registry import ToolDefinition, get_registry

        # Register tool_a -> srv1 in the static registry
        reg = get_registry()
        reg.register(ToolDefinition(name="tool_a", server_key="srv1"))

        http = AsyncMock(spec=httpx.AsyncClient)

        async def _get(url: str, timeout: float = 5.0) -> MagicMock:
            if "srv1" in url:
                return _resp(
                    200,
                    {
                        "tools": [
                            {"name": "tool_a", "description": "d", "inputSchema": {}}
                        ]
                    },
                )
            return _resp(
                200,
                {"tools": [{"name": "tool_a", "description": "d", "inputSchema": {}}]},
            )

        http.get = AsyncMock(side_effect=_get)
        ctx = _make_ctx(
            {
                "srv1": _server("http://srv1:9000"),
                "srv2": _server("http://srv2:9000"),
            },
            http,
            security_profile=SecurityProfile.LOCAL,
        )
        ctx.cfg.tool.tool_definitions_strict = False

        result = await McpToolDiscoveryService(ctx).discover_all()

        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        drift_findings = [f for f in mcp_findings if "drift" in f.message.lower()]
        assert len(drift_findings) >= 1
        assert any("Live routing drift" in f.message for f in drift_findings)


# ── unified severity matrix ────────────────────────────────────────────────────


class TestUnifiedSeverity:
    @pytest.mark.parametrize(
        "strict, profile, expected_status",
        [
            (False, SecurityProfile.LOCAL, StartupCheckStatus.WARNING),
            (False, SecurityProfile.PRODUCTION, StartupCheckStatus.FATAL),
            (True, SecurityProfile.LOCAL, StartupCheckStatus.FATAL),
            (True, SecurityProfile.PRODUCTION, StartupCheckStatus.FATAL),
        ],
    )
    @pytest.mark.asyncio
    async def test_severity_unified_for_duplicates(
        self,
        strict: bool,
        profile: SecurityProfile,
        expected_status: StartupCheckStatus,
    ) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)

        async def _get(url: str, timeout: float = 5.0) -> MagicMock:
            return _resp(
                200,
                {
                    "tools": [
                        {"name": "dup_tool", "description": "d", "inputSchema": {}}
                    ]
                },
            )

        http.get = AsyncMock(side_effect=_get)
        ctx = _make_ctx(
            {
                "srv1": _server("http://srv1:9000"),
                "srv2": _server("http://srv2:9000"),
            },
            http,
            security_profile=profile,
        )
        ctx.cfg.tool.tool_definitions_strict = strict

        result = await McpToolDiscoveryService(ctx).discover_all()

        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        dup_findings = [f for f in mcp_findings if "duplicate" in f.message.lower()]
        assert len(dup_findings) == 1
        assert dup_findings[0].status == expected_status


# ── tool definitions check surfaces as outcome, not exception ──────────────────


@pytest.mark.asyncio
async def test_tool_definitions_check_surfaces_as_outcome_not_exception(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "agent.services.mcp_tool_discovery._check_tool_definitions",
        AsyncMock(side_effect=RuntimeError("boom")),
    )

    http = AsyncMock(spec=httpx.AsyncClient)

    async def _get(url: str, timeout: float = 5.0) -> MagicMock:
        return _resp(
            200,
            {"tools": [{"name": "grep", "description": "d", "inputSchema": {}}]},
        )

    http.get = AsyncMock(side_effect=_get)
    ctx = _make_ctx({"srv": _server()}, http)
    ctx.cfg.tool.tool_definitions_strict = False

    result = await McpToolDiscoveryService(ctx).discover_all()

    mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
    tool_defs_findings = [f for f in mcp_findings if "boom" in f.message]
    assert len(tool_defs_findings) == 1
    assert tool_defs_findings[0].status == StartupCheckStatus.WARNING
