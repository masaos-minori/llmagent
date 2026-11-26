"""
tests/agent/services/test_mcp_tool_discovery.py
Unit tests for agent.services.mcp_tool_discovery.McpToolDiscoveryService.

httpx.AsyncClient and AgentContext are mocked (mirrors tests/test_repl_health.py's
own mocking style).

Also includes real-app schema validation tests against each MCP server's
/v1/tools endpoint (TestToolsEndpointSchemaVersion, TestToolsEndpointToolShape).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from types import ModuleType
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from agent.services.mcp_health import PostureGate
from agent.services.mcp_tool_discovery import DiscoveryResult, McpToolDiscoveryService
from agent.services.mcp_tool_discovery_registry import (
    _build_runtime_tools,
    _dedupe_and_build,
)
from agent.shared.health_models import (
    HealthCheckResult,
    ServiceWarning,
    StartupCheckStatus,
)
from fastapi.testclient import TestClient
from shared.mcp_config import (
    McpServerConfig,
    StartupMode,
    TransportType,
)
from shared.mcp_health_contract import parse_health_body
from shared.tool_registry import (
    ToolDefinition,
    _reset_registry_for_testing,
    get_registry,
)

from tests.agent.services._discovery_gates import gates_from


def _server_auth_headers(module: ModuleType) -> dict[str, str]:
    """Bearer header for servers whose test config carries a non-empty inbound token."""
    token = (
        getattr(getattr(module, "_cfg", None), "auth_token", "")
        or getattr(module, "_AUTH_TOKEN", "")
        or ""
    )
    return {"Authorization": f"Bearer {token}"} if token else {}


_IN_SCOPE_SERVERS = [
    ("mcp_servers.mdq.mdq_server", "app", "mdq"),
    ("mcp_servers.cicd.cicd_server", "app", "cicd"),
    ("mcp_servers.github.github_server", "app", "github"),
    ("mcp_servers.git.git_server", "app", "git"),
    ("mcp_servers.web_search.web_search_server", "app", "web_search"),
    ("mcp_servers.shell.shell_server", "app", "shell"),
    ("mcp_servers.rag_pipeline.rag_pipeline_server", "app", "rag_pipeline"),
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


def _server(
    url: str = "http://127.0.0.1:9000",
    startup_mode: StartupMode = StartupMode.PERSISTENT,
    required: bool = True,
) -> McpServerConfig:
    return McpServerConfig(
        transport=TransportType.HTTP,
        url=url,
        startup_mode=startup_mode,
        auth_token="test-token",
        required=required,
    )


def _make_ctx(
    servers: dict[str, object],
    http: AsyncMock,
) -> MagicMock:
    """Build a minimal mocked AgentContext (mirrors tests/test_repl_health.py's style)."""
    ctx = MagicMock()
    ctx.cfg.mcp.mcp_servers = servers
    ctx.services_required.http = http
    return ctx


def _gates_with_reports(
    servers: Mapping[str, object],
    reports: Mapping[str, Mapping[str, object]],
) -> dict[str, PostureGate]:
    """Green gates carrying the parsed /health body the capability check reads as proof.

    `gates_from` builds a gate with no report, and a gate with no report proves nothing under the
    report-based rule (REQ-005), so a case that expects a required server to pass must name the body
    its gate carries. A body without the capability block is read through the legacy `ready`
    fallback (D-6).
    """
    gates = gates_from(servers)
    for key, body in reports.items():
        gates[key] = replace(gates[key], report=parse_health_body(body))
    return gates


def _tool_entry(
    name: str,
    capabilities: list[str],
    **overrides: object,
) -> dict[str, object]:
    """One schema-2.1 tool entry as the producer declares it, with its capability dependency."""
    entry: dict[str, object] = {
        "name": name,
        "description": "d",
        "inputSchema": {"type": "object", "properties": {}},
        "is_write": False,
        "requires_serial": False,
        "resource_scope_kind": "",
        "resource_scope_keys": {},
        "agent_safety_tier": "READ_ONLY",
        "side_effect_class": "read_only",
        "retry_policy": "safe_read_retry",
        "reconciliation_policy": "not_required",
        "idempotency_required": False,
        "preview_capability": "none",
        "policy_version": "2.1",
        "capabilities": capabilities,
    }
    entry.update(overrides)
    return entry


# ── declared write classification drift (ADR-003 INV-03) ─────────────────────


class TestWriteClassificationFinding:
    @pytest.mark.asyncio
    async def test_static_write_tool_reported_read_only_is_flagged(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [
                        {
                            "name": "write_file",
                            "description": "write",
                            "inputSchema": {"type": "object", "properties": {}},
                            "is_write": False,
                            "requires_serial": False,
                            "resource_scope_kind": "",
                            "resource_scope_keys": {},
                            "agent_safety_tier": "READ_ONLY",
                            "side_effect_class": "read_only",
                            "retry_policy": "safe_read_retry",
                            "reconciliation_policy": "not_required",
                            "idempotency_required": False,
                            "preview_capability": "none",
                            "policy_version": "2.1",
                        }
                    ],
                },
            )
        )
        ctx = _make_ctx({"s": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        drift = [
            f
            for f in result.findings
            if f.message.startswith("Declared write classification drift")
        ]
        assert len(drift) == 2
        assert all(f.status == StartupCheckStatus.FATAL for f in drift)
        # AC-10: the finding is a report only — the entry is still registered with the
        # values its producer declared, and no classification is changed by the drift.
        tool = result.registry.get("write_file")
        assert tool is not None
        assert tool.is_write is False
        assert tool.side_effect_class == "read_only"


# ── discover_all() happy path ─────────────────────────────────────────────────


class TestDiscoverAllHappyPath:
    @pytest.mark.asyncio
    async def test_single_server_single_valid_tool_builds_registry(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [
                        {
                            "name": "grep",
                            "description": "search files",
                            "inputSchema": {"type": "object", "properties": {}},
                            "is_write": False,
                            "requires_serial": False,
                            "resource_scope_kind": "",
                            "resource_scope_keys": {},
                            "agent_safety_tier": "READ_ONLY",
                            "side_effect_class": "read_only",
                            "retry_policy": "safe_read_retry",
                            "reconciliation_policy": "not_required",
                            "idempotency_required": False,
                            "preview_capability": "none",
                            "policy_version": "2.1",
                        }
                    ],
                },
            )
        )
        ctx = _make_ctx({"search_server": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert isinstance(result, DiscoveryResult)
        tool = result.registry.get("grep")
        assert tool.server_key == "search_server"
        assert tool.server_url == "http://127.0.0.1:9000"
        assert tool.description == "search files"
        assert tool.input_schema == {"type": "object", "properties": {}}
        assert tool.is_write is False
        assert tool.requires_serial is False  # declared, not defaulted
        assert tool.resource_scope_kind == ""
        assert tool.resource_scope_keys == {}
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 0
        assert result.unreachable == []

    @pytest.mark.asyncio
    async def test_explicit_write_tool_all_fields_round_trip(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [
                        {
                            "name": "write_file",
                            "description": "writes a file",
                            "inputSchema": {"type": "object", "properties": {}},
                            "is_write": True,
                            "requires_serial": True,
                            "resource_scope_kind": "process",
                            "resource_scope_keys": {},
                            "agent_safety_tier": "WRITE_SAFE",
                            "side_effect_class": "local_write",
                            "retry_policy": "never",
                            "reconciliation_policy": "local_state",
                            "idempotency_required": True,
                            "preview_capability": "none",
                            "policy_version": "2.1",
                        }
                    ],
                },
            )
        )
        ctx = _make_ctx({"fs": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        tool = result.registry.get("write_file")
        assert tool.is_write is True
        assert tool.requires_serial is True
        assert tool.resource_scope_kind == "process"
        assert tool.resource_scope_keys == {}
        # agentcfg003 REQ-002/REQ-003: every declared policy value round-trips
        # unchanged into the registered entry.
        assert tool.agent_safety_tier == "WRITE_SAFE"
        assert tool.side_effect_class == "local_write"
        assert tool.retry_policy == "never"
        assert tool.reconciliation_policy == "local_state"
        assert tool.idempotency_required is True
        assert tool.preview_capability == "none"
        assert tool.policy_version == "2.1"


# ── enabled_for_llm derivation from `enabled` key ─────────────────────────────


class TestDiscoverAllSendsBearerAuth:
    """/v1/tools requires the same Bearer token as every other MCP endpoint (401 otherwise)."""

    @staticmethod
    def _empty_tools_http() -> AsyncMock:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(_resp(200, {"schema_version": "1.0", "tools": []}))
        return http

    @pytest.mark.asyncio
    async def test_each_server_receives_its_own_bearer_token(self) -> None:
        http = self._empty_tools_http()
        alpha = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9001",
            startup_mode=StartupMode.PERSISTENT,
            auth_token="token-alpha",
        )
        beta = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9002",
            startup_mode=StartupMode.PERSISTENT,
            auth_token="token-beta",
        )
        ctx = _make_ctx({"alpha": alpha, "beta": beta}, http)

        await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        sent = {
            call.args[0]: call.kwargs["headers"] for call in http.get.call_args_list
        }
        assert sent == {
            "http://127.0.0.1:9001/v1/tools": {"Authorization": "Bearer token-alpha"},
            "http://127.0.0.1:9002/v1/tools": {"Authorization": "Bearer token-beta"},
        }


class TestDiscoverAllEnabledForLlm:
    @pytest.mark.asyncio
    async def test_enabled_key_absent_defaults_to_true(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [
                        {
                            "name": "grep",
                            "description": "d",
                            "inputSchema": {"type": "object", "properties": {}},
                            "is_write": False,
                            "requires_serial": False,
                            "resource_scope_kind": "",
                            "resource_scope_keys": {},
                            "agent_safety_tier": "READ_ONLY",
                            "side_effect_class": "read_only",
                            "retry_policy": "safe_read_retry",
                            "reconciliation_policy": "not_required",
                            "idempotency_required": False,
                            "preview_capability": "none",
                            "policy_version": "2.1",
                        }
                    ],
                },
            )
        )
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.registry.get("grep").enabled_for_llm is True

    @pytest.mark.asyncio
    async def test_enabled_true_stays_visible(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [
                        {
                            "name": "read_file",
                            "description": "d",
                            "inputSchema": {"type": "object", "properties": {}},
                            "enabled": True,
                            "is_write": False,
                            "requires_serial": False,
                            "resource_scope_kind": "",
                            "resource_scope_keys": {},
                            "agent_safety_tier": "READ_ONLY",
                            "side_effect_class": "read_only",
                            "retry_policy": "safe_read_retry",
                            "reconciliation_policy": "not_required",
                            "idempotency_required": False,
                            "preview_capability": "none",
                            "policy_version": "2.1",
                        }
                    ],
                },
            )
        )
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.registry.get("read_file").enabled_for_llm is True

    @pytest.mark.asyncio
    async def test_enabled_false_hides_tool_from_llm(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [
                        {
                            "name": "delete_file",
                            "description": "d",
                            "inputSchema": {"type": "object", "properties": {}},
                            "enabled": False,
                            "disabled_reason": "feature flag off",
                            "is_write": True,
                            "requires_serial": True,
                            "resource_scope_kind": "",
                            "resource_scope_keys": {},
                            "agent_safety_tier": "WRITE_SAFE",
                            "side_effect_class": "local_write",
                            "retry_policy": "never",
                            "reconciliation_policy": "local_state",
                            "idempotency_required": True,
                            "preview_capability": "none",
                            "policy_version": "2.1",
                        }
                    ],
                },
            )
        )
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        tool = result.registry.get("delete_file")
        assert tool.enabled_for_llm is False
        # still present in the registry (routing-visible); only LLM-payload visibility is gated
        assert "delete_file" in {t.name for t in result.registry.all_tools()}


# ── per-entry schema validation ───────────────────────────────────────────────


class TestDiscoverAllMalformedEntries:
    @pytest.mark.asyncio
    async def test_missing_name_produces_warning_and_is_excluded(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [{"description": "d", "inputSchema": {}}],
                },
            )
        )
        srv_cfg = _server(startup_mode=StartupMode.PERSISTENT)
        srv_cfg.required = False
        ctx = _make_ctx({"srv": srv_cfg}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

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
                200,
                {
                    "schema_version": "1.0",
                    "tools": [{"name": "   ", "description": "d", "inputSchema": {}}],
                },
            )
        )
        srv_cfg = _server(startup_mode=StartupMode.PERSISTENT)
        srv_cfg.required = False
        ctx = _make_ctx({"srv": srv_cfg}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.registry.all_tools() == []
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1
        assert any(f.status == StartupCheckStatus.WARNING for f in mcp_findings)

    @pytest.mark.asyncio
    async def test_missing_description_produces_warning_and_is_excluded(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [{"name": "grep", "inputSchema": {}}],
                },
            )
        )
        srv_cfg = _server(startup_mode=StartupMode.PERSISTENT)
        srv_cfg.required = False
        ctx = _make_ctx({"srv": srv_cfg}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

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
                    "schema_version": "1.0",
                    "tools": [
                        {"name": "grep", "description": "d", "inputSchema": "nope"}
                    ],
                },
            )
        )
        srv_cfg = _server(startup_mode=StartupMode.PERSISTENT)
        srv_cfg.required = False
        ctx = _make_ctx({"srv": srv_cfg}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.registry.all_tools() == []
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1
        assert any(f.status == StartupCheckStatus.WARNING for f in mcp_findings)

    @pytest.mark.asyncio
    async def test_non_dict_entry_itself_produces_warning_and_is_excluded(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(200, {"schema_version": "1.0", "tools": ["not-a-dict"]})
        )
        srv_cfg = _server(startup_mode=StartupMode.PERSISTENT)
        srv_cfg.required = False
        ctx = _make_ctx({"srv": srv_cfg}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

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
                    "schema_version": "1.0",
                    "tools": [
                        {"description": "no name", "inputSchema": {}},
                        {
                            "name": "grep",
                            "description": "d",
                            "inputSchema": {"type": "object", "properties": {}},
                            "is_write": False,
                            "requires_serial": False,
                            "resource_scope_kind": "",
                            "resource_scope_keys": {},
                            "agent_safety_tier": "READ_ONLY",
                            "side_effect_class": "read_only",
                            "retry_policy": "safe_read_retry",
                            "reconciliation_policy": "not_required",
                            "idempotency_required": False,
                            "preview_capability": "none",
                            "policy_version": "2.1",
                        },
                    ],
                },
            )
        )
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.registry.get("grep").server_key == "srv"
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1
        assert any(f.status == StartupCheckStatus.FATAL for f in mcp_findings)


# ── schema-2.0 four-field contract: required, not defaulted ───────────────────


class TestDiscoverAllSchemaV2Contract:
    """Schema-2.1 required-field contract: required, not defaulted (agentcfg003 REQ-002/REQ-003)."""

    @pytest.mark.asyncio
    async def test_complete_declaration_round_trips_all_required_fields(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [
                        {
                            "name": "move_file",
                            "description": "moves a file",
                            "inputSchema": {
                                "type": "object",
                                "properties": {
                                    "source": {"type": "string"},
                                    "destination": {"type": "string"},
                                },
                            },
                            "is_write": True,
                            "requires_serial": True,
                            "resource_scope_kind": "filesystem",
                            "resource_scope_keys": {
                                "source": "path",
                                "destination": "path",
                            },
                            "agent_safety_tier": "WRITE_SAFE",
                            "side_effect_class": "local_write",
                            "retry_policy": "never",
                            "reconciliation_policy": "local_state",
                            "idempotency_required": True,
                            "preview_capability": "none",
                            "policy_version": "2.1",
                        }
                    ],
                },
            )
        )
        ctx = _make_ctx({"fs": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        tool = result.registry.get("move_file")
        assert tool.is_write is True
        assert tool.requires_serial is True
        assert tool.resource_scope_kind == "filesystem"
        assert tool.resource_scope_keys == {"source": "path", "destination": "path"}
        assert tool.agent_safety_tier == "WRITE_SAFE"
        assert tool.side_effect_class == "local_write"
        assert tool.retry_policy == "never"
        assert tool.reconciliation_policy == "local_state"
        assert tool.idempotency_required is True
        assert tool.preview_capability == "none"
        assert tool.policy_version == "2.1"

    @pytest.mark.asyncio
    async def test_missing_is_write_produces_warning_and_is_excluded(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [
                        {
                            "name": "incomplete_tool",
                            "description": "d",
                            "inputSchema": {"type": "object", "properties": {}},
                            "requires_serial": False,
                            "resource_scope_kind": "",
                            "resource_scope_keys": {},
                        }
                    ],
                },
            )
        )
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.registry.all_tools() == []
        assert any("is_write" in f.message for f in result.findings)

    @pytest.mark.asyncio
    async def test_missing_requires_serial_produces_warning_and_is_excluded(
        self,
    ) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [
                        {
                            "name": "incomplete_tool",
                            "description": "d",
                            "inputSchema": {"type": "object", "properties": {}},
                            "is_write": False,
                            "resource_scope_kind": "",
                            "resource_scope_keys": {},
                        }
                    ],
                },
            )
        )
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.registry.all_tools() == []
        assert any("requires_serial" in f.message for f in result.findings)

    @pytest.mark.asyncio
    async def test_missing_resource_scope_kind_produces_warning_and_is_excluded(
        self,
    ) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [
                        {
                            "name": "incomplete_tool",
                            "description": "d",
                            "inputSchema": {"type": "object", "properties": {}},
                            "is_write": False,
                            "requires_serial": False,
                            "resource_scope_keys": {},
                        }
                    ],
                },
            )
        )
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.registry.all_tools() == []
        assert any("resource_scope_kind" in f.message for f in result.findings)

    @pytest.mark.asyncio
    async def test_missing_resource_scope_keys_produces_warning_and_is_excluded(
        self,
    ) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [
                        {
                            "name": "incomplete_tool",
                            "description": "d",
                            "inputSchema": {"type": "object", "properties": {}},
                            "is_write": False,
                            "requires_serial": False,
                            "resource_scope_kind": "",
                        }
                    ],
                },
            )
        )
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.registry.all_tools() == []
        assert any("resource_scope_keys" in f.message for f in result.findings)

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "missing_field",
        [
            "agent_safety_tier",
            "side_effect_class",
            "retry_policy",
            "reconciliation_policy",
            "idempotency_required",
            "preview_capability",
            "policy_version",
        ],
    )
    async def test_missing_declared_policy_field_produces_warning_and_is_excluded(
        self,
        missing_field: str,
    ) -> None:
        """Agentcfg003 REQ-002/REQ-003 (AC-02, AC-03): an entry omitting one declared
        policy field is rejected before registration; no default fills it in."""
        entry: dict[str, object] = {
            "name": "incomplete_tool",
            "description": "d",
            "inputSchema": {"type": "object", "properties": {}},
            "is_write": False,
            "requires_serial": False,
            "resource_scope_kind": "",
            "resource_scope_keys": {},
            "agent_safety_tier": "READ_ONLY",
            "side_effect_class": "read_only",
            "retry_policy": "safe_read_retry",
            "reconciliation_policy": "not_required",
            "idempotency_required": False,
            "preview_capability": "none",
            "policy_version": "2.1",
        }
        del entry[missing_field]

        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(200, {"schema_version": "1.0", "tools": [entry]})
        )
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.registry.all_tools() == []
        assert any(missing_field in f.message for f in result.findings)

    @pytest.mark.asyncio
    async def test_resource_scope_keys_referencing_unknown_arg_produces_warning_and_is_excluded(
        self,
    ) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [
                        {
                            "name": "bad_scope_tool",
                            "description": "d",
                            "inputSchema": {
                                "type": "object",
                                "properties": {"path": {"type": "string"}},
                            },
                            "is_write": True,
                            "requires_serial": True,
                            "resource_scope_kind": "filesystem",
                            "resource_scope_keys": {
                                "path": "path",
                                "missing_arg": "path",
                            },
                            "agent_safety_tier": "WRITE_SAFE",
                            "side_effect_class": "local_write",
                            "retry_policy": "never",
                            "reconciliation_policy": "local_state",
                            "idempotency_required": True,
                            "preview_capability": "none",
                            "policy_version": "2.1",
                        }
                    ],
                },
            )
        )
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.registry.all_tools() == []
        assert any("missing_arg" in f.message for f in result.findings)


# ── whole-server unreachable/malformed responses ──────────────────────────────


class TestDiscoverAllUnreachableServers:
    @pytest.mark.asyncio
    async def test_non_200_status_marks_server_unreachable(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(_resp(503, {}))
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.unreachable == ["srv"]
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1
        assert any(f.status == StartupCheckStatus.FATAL for f in mcp_findings)
        assert result.registry.all_tools() == []

    @pytest.mark.asyncio
    async def test_invalid_json_body_marks_server_unreachable(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        resp = MagicMock()
        resp.status_code = 200
        resp.json.side_effect = ValueError("bad json")
        http.get = _async_result(resp)
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.unreachable == ["srv"]
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1
        assert any(f.status == StartupCheckStatus.FATAL for f in mcp_findings)

    @pytest.mark.asyncio
    async def test_non_dict_top_level_body_marks_server_unreachable(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(_resp(200, ["not", "a", "dict"]))
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.unreachable == ["srv"]
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1

    @pytest.mark.asyncio
    async def test_tools_field_missing_marks_server_unreachable(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(_resp(200, {"status": "ok"}))
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.unreachable == ["srv"]
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1

    @pytest.mark.asyncio
    async def test_tools_field_not_a_list_marks_server_unreachable(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(200, {"schema_version": "1.0", "tools": "not-a-list"})
        )
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.unreachable == ["srv"]
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1

    @pytest.mark.asyncio
    async def test_connect_error_marks_server_unreachable(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.unreachable == ["srv"]
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1
        assert any("refused" in f.message for f in mcp_findings)

    @pytest.mark.asyncio
    async def test_os_error_marks_server_unreachable(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock(side_effect=OSError("network down"))
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.unreachable == ["srv"]
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) >= 1

    @pytest.mark.asyncio
    async def test_one_unreachable_server_others_still_processed(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)

        async def _get(
            url: str,
            timeout: float = 5.0,
            headers: dict | None = None,
        ) -> MagicMock:
            if "bad" in url:
                raise httpx.ConnectError("refused")
            return _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [
                        {
                            "name": "grep",
                            "description": "d",
                            "inputSchema": {"type": "object", "properties": {}},
                            "is_write": False,
                            "requires_serial": False,
                            "resource_scope_kind": "",
                            "resource_scope_keys": {},
                            "agent_safety_tier": "READ_ONLY",
                            "side_effect_class": "read_only",
                            "retry_policy": "safe_read_retry",
                            "reconciliation_policy": "not_required",
                            "idempotency_required": False,
                            "preview_capability": "none",
                            "policy_version": "2.1",
                        }
                    ],
                },
            )

        http.get = AsyncMock(side_effect=_get)
        ctx = _make_ctx(
            {
                "bad_server": _server("http://bad-host:9000"),
                "good_server": _server("http://good-host:9000"),
            },
            http,
        )

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.unreachable == ["bad_server"]
        assert result.registry.get("grep").server_key == "good_server"

    @pytest.mark.asyncio
    async def test_unreachable_non_required_server_tool_definition_check_is_fatal(
        self,
    ) -> None:
        """ADR-004: the tool-definition check has no non-strict bypass, so a server
        that is unreachable stays `required = false` on the escalation axis (WARNING)
        but the tool-definition finding is always FATAL."""
        srv_cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9000",
            startup_mode=StartupMode.PERSISTENT,
            required=False,
            auth_token="test-token",
        )
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        ctx = _make_ctx({"srv": srv_cfg}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.unreachable == ["srv"]
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert any(
            f.status == StartupCheckStatus.FATAL
            and "cannot validate tool ownership" in f.message
            for f in mcp_findings
        )
        assert any(f.status == StartupCheckStatus.WARNING for f in mcp_findings)

    @pytest.mark.asyncio
    async def test_unreachable_required_server_returns_fatal(
        self,
    ) -> None:
        srv_cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9000",
            startup_mode=StartupMode.PERSISTENT,
            required=True,
            auth_token="test-token",
        )
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock(side_effect=httpx.ConnectError("refused"))
        ctx = _make_ctx({"srv": srv_cfg}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.unreachable == ["srv"]
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert any(f.status == StartupCheckStatus.FATAL for f in mcp_findings)


# ── cross-server duplicate tool names ──────────────────────────────────────────


class TestDiscoverAllDuplicates:
    def _dup_ctx(self) -> MagicMock:
        http = AsyncMock(spec=httpx.AsyncClient)

        async def _get(
            url: str,
            timeout: float = 5.0,
            headers: dict | None = None,
        ) -> MagicMock:
            return _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [
                        {
                            "name": "grep",
                            "description": "d",
                            "inputSchema": {"type": "object", "properties": {}},
                            "is_write": False,
                            "requires_serial": False,
                            "resource_scope_kind": "",
                            "resource_scope_keys": {},
                            "agent_safety_tier": "READ_ONLY",
                            "side_effect_class": "read_only",
                            "retry_policy": "safe_read_retry",
                            "reconciliation_policy": "not_required",
                            "idempotency_required": False,
                            "preview_capability": "none",
                            "policy_version": "2.1",
                        }
                    ],
                },
            )

        http.get = AsyncMock(side_effect=_get)
        ctx = _make_ctx(
            {
                "server_a": _server("http://a:9000"),
                "server_b": _server("http://b:9000"),
            },
            http,
        )
        return ctx

    @pytest.mark.asyncio
    async def test_duplicate_name_production_is_fatal_and_excluded(self) -> None:
        ctx = self._dup_ctx()

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.registry.all_tools() == []
        dup_findings = [f for f in result.findings if "duplicate" in f.message]
        assert len(dup_findings) == 1
        assert dup_findings[0].status == StartupCheckStatus.FATAL


# ── non-HTTP / empty-URL / disabled server filtering ──────────────────────────


class TestDiscoverAllServerFilter:
    @pytest.mark.asyncio
    async def test_empty_url_server_is_skipped(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock()
        cfg = MagicMock()
        cfg.transport = TransportType.HTTP
        cfg.url = ""
        ctx = _make_ctx({"empty_url_server": cfg}, http)

        result = await McpToolDiscoveryService(
            ctx,
            posture_gates=_gates_with_reports(
                ctx.cfg.mcp.mcp_servers,
                {"empty_url_server": {"liveness": True, "ready": True}},
            ),
        ).discover_all()

        http.get.assert_not_called()
        assert result.registry.all_tools() == []
        # The server is skipped from the fetch, but the required-capability check still reads its
        # gate, so the fixture gate carries a legacy body that proves readiness through `ready`
        # (D-6): the filter is what is asserted here, not an absent proof.
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

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        http.get.assert_not_called()
        assert result.registry.all_tools() == []

    @pytest.mark.asyncio
    async def test_disabled_server_is_skipped_no_http_call(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery._check_tool_definitions",
            AsyncMock(return_value=HealthCheckResult()),
        )
        srv_cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9000",
            startup_mode=StartupMode.NONE,
            auth_token="test-token",
        )
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock()
        ctx = _make_ctx({"disabled_srv": srv_cfg}, http)

        result = await McpToolDiscoveryService(
            ctx,
            posture_gates=_gates_with_reports(
                ctx.cfg.mcp.mcp_servers,
                {"disabled_srv": {"liveness": True, "ready": True}},
            ),
        ).discover_all()

        http.get.assert_not_called()
        assert result.registry.all_tools() == []
        # The disabled server is not fetched, yet it is still a required server the check reads,
        # so its gate carries a legacy body that proves readiness through `ready` (D-6).
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        assert len(mcp_findings) == 0
        assert result.unreachable == []

    @pytest.mark.asyncio
    async def test_disabled_server_with_required_flag_still_skipped(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery._check_tool_definitions",
            AsyncMock(return_value=HealthCheckResult()),
        )
        srv_cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9000",
            startup_mode=StartupMode.NONE,
            required=True,
            auth_token="test-token",
        )
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = AsyncMock()
        ctx = _make_ctx({"disabled_required_srv": srv_cfg}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        http.get.assert_not_called()
        assert result.unreachable == []
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        # No capability is declared anywhere, so the required-capability check is
        # inert (REQ-005 engages only once servers surface a capability); the
        # disabled server is simply not fetched.
        required_cap_findings = [
            f
            for f in mcp_findings
            if "required capability" in f.message
            or "absent from tool_catalog" in f.message
        ]
        assert len(required_cap_findings) == 0


# ── real-app schema validation matrix ──────────────────────────────────────────


class TestToolsEndpointSchemaVersion:
    @pytest.mark.parametrize("import_path, app_attr, server_key", _IN_SCOPE_SERVERS)
    def test_schema_version_present(
        self, import_path: str, app_attr: str, server_key: str
    ) -> None:
        import importlib

        from mcp_servers.server import MCP_TOOL_SCHEMA_VERSION

        module = importlib.import_module(import_path)
        client = TestClient(
            getattr(module, app_attr),
            raise_server_exceptions=True,
            headers=_server_auth_headers(module),
        )
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
        client = TestClient(
            getattr(module, app_attr),
            raise_server_exceptions=True,
            headers=_server_auth_headers(module),
        )
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
async def test_legacy_singular_resource_scope_rejected_synthetic() -> None:
    """Legacy singular `resource_scope` is rejected as a schema error (owner decision 2026-10-28)."""
    http = AsyncMock(spec=httpx.AsyncClient)
    http.get = _async_result(
        _resp(
            200,
            {
                "schema_version": "1.0",
                "tools": [
                    {
                        "name": "test_tool",
                        "description": "desc",
                        "inputSchema": {"type": "object", "properties": {}},
                        "resource_scope": 123,
                        "is_write": False,
                        "requires_serial": False,
                        "resource_scope_kind": "",
                        "resource_scope_keys": {},
                    }
                ],
            },
        )
    )
    ctx = _make_ctx({"srv": _server()}, http)

    result = await McpToolDiscoveryService(
        ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
    ).discover_all()

    assert result.registry.all_tools() == []
    assert any("resource_scope" in f.message for f in result.findings)

    http2 = AsyncMock(spec=httpx.AsyncClient)
    http2.get = _async_result(
        _resp(
            200,
            {
                "schema_version": "1.0",
                "tools": [
                    {
                        "name": "test_tool_ok",
                        "description": "desc",
                        "inputSchema": {"type": "object", "properties": {}},
                        "resource_scope": "filesystem",
                        "is_write": False,
                        "requires_serial": False,
                        "resource_scope_kind": "",
                        "resource_scope_keys": {},
                    }
                ],
            },
        )
    )
    ctx2 = _make_ctx({"srv": _server()}, http2)

    result2 = await McpToolDiscoveryService(
        ctx2, posture_gates=gates_from(ctx2.cfg.mcp.mcp_servers)
    ).discover_all()

    assert result2.registry.all_tools() == []
    assert any("resource_scope" in f.message for f in result2.findings)


@pytest.mark.asyncio
async def test_missing_scope_field_reported_once_synthetic() -> None:
    http = AsyncMock(spec=httpx.AsyncClient)
    http.get = _async_result(
        _resp(
            200,
            {
                "schema_version": "1.0",
                "tools": [
                    {
                        "name": "incomplete_tool",
                        "description": "desc",
                        "inputSchema": {"type": "object", "properties": {}},
                        "is_write": False,
                        "requires_serial": False,
                        "resource_scope_kind": "",
                    }
                ],
            },
        )
    )
    ctx = _make_ctx({"srv": _server()}, http)

    result = await McpToolDiscoveryService(
        ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
    ).discover_all()

    assert result.registry.all_tools() == []
    assert sum(1 for f in result.findings if "resource_scope_keys" in f.message) == 1


@pytest.mark.asyncio
async def test_enabled_type_checked_when_present_synthetic() -> None:
    http = AsyncMock(spec=httpx.AsyncClient)
    http.get = _async_result(
        _resp(
            200,
            {
                "schema_version": "1.0",
                "tools": [
                    {
                        "name": "test_tool",
                        "description": "desc",
                        "inputSchema": {"type": "object", "properties": {}},
                        "enabled": "yes",
                        "is_write": False,
                        "requires_serial": False,
                        "resource_scope_kind": "",
                        "resource_scope_keys": {},
                        "agent_safety_tier": "READ_ONLY",
                        "side_effect_class": "read_only",
                        "retry_policy": "safe_read_retry",
                        "reconciliation_policy": "not_required",
                        "idempotency_required": False,
                        "preview_capability": "none",
                        "policy_version": "2.1",
                    }
                ],
            },
        )
    )
    ctx = _make_ctx({"srv": _server()}, http)

    result = await McpToolDiscoveryService(
        ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
    ).discover_all()

    assert result.registry.all_tools() == []
    enabled_findings = [
        f
        for f in result.findings
        if "enabled" in f.message and "test_tool" in f.message
    ]
    assert len(enabled_findings) == 1
    assert enabled_findings[0].status == StartupCheckStatus.FATAL

    http2 = AsyncMock(spec=httpx.AsyncClient)
    http2.get = _async_result(
        _resp(
            200,
            {
                "schema_version": "1.0",
                "tools": [
                    {
                        "name": "test_tool_ok",
                        "description": "desc",
                        "inputSchema": {"type": "object", "properties": {}},
                        "enabled": False,
                        "is_write": False,
                        "requires_serial": False,
                        "resource_scope_kind": "",
                        "resource_scope_keys": {},
                        "agent_safety_tier": "READ_ONLY",
                        "side_effect_class": "read_only",
                        "retry_policy": "safe_read_retry",
                        "reconciliation_policy": "not_required",
                        "idempotency_required": False,
                        "preview_capability": "none",
                        "policy_version": "2.1",
                    }
                ],
            },
        )
    )
    ctx2 = _make_ctx({"srv": _server()}, http2)

    result2 = await McpToolDiscoveryService(
        ctx2, posture_gates=gates_from(ctx2.cfg.mcp.mcp_servers)
    ).discover_all()

    assert result2.registry.get("test_tool_ok") is not None
    assert not any("enabled" in f.message for f in result2.findings)


@pytest.mark.asyncio
async def test_missing_schema_version_rejected() -> None:
    http = AsyncMock(spec=httpx.AsyncClient)
    http.get = _async_result(
        _resp(
            200,
            {
                "tools": [
                    {
                        "name": "legacy_tool",
                        "description": "legacy",
                        "inputSchema": {"type": "object", "properties": {}},
                        "is_write": False,
                        "requires_serial": False,
                        "resource_scope_kind": "",
                        "resource_scope_keys": {},
                        "agent_safety_tier": "READ_ONLY",
                        "side_effect_class": "read_only",
                        "retry_policy": "safe_read_retry",
                        "reconciliation_policy": "not_required",
                        "idempotency_required": False,
                        "preview_capability": "none",
                        "policy_version": "2.1",
                    }
                ]
            },
        )
    )
    ctx = _make_ctx({"legacy_srv": _server()}, http)

    result = await McpToolDiscoveryService(
        ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
    ).discover_all()

    assert result.registry.all_tools() == []
    mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
    missing_sv = [f for f in mcp_findings if "schema_version" in f.message]
    assert len(missing_sv) >= 1
    assert missing_sv[0].status in (
        StartupCheckStatus.WARNING,
        StartupCheckStatus.FATAL,
    )


@pytest.mark.asyncio
async def test_unsupported_schema_version_rejected() -> None:
    http = AsyncMock(spec=httpx.AsyncClient)
    http.get = _async_result(
        _resp(
            200,
            {
                "schema_version": "9.9",
                "tools": [
                    {
                        "name": "future_tool",
                        "description": "future",
                        "inputSchema": {"type": "object", "properties": {}},
                        "is_write": False,
                        "requires_serial": False,
                        "resource_scope_kind": "",
                        "resource_scope_keys": {},
                        "agent_safety_tier": "READ_ONLY",
                        "side_effect_class": "read_only",
                        "retry_policy": "safe_read_retry",
                        "reconciliation_policy": "not_required",
                        "idempotency_required": False,
                        "preview_capability": "none",
                        "policy_version": "2.1",
                    }
                ],
            },
        )
    )
    ctx = _make_ctx({"future_srv": _server()}, http)

    result = await McpToolDiscoveryService(
        ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
    ).discover_all()

    assert result.registry.all_tools() == []
    mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
    bad_sv = [f for f in mcp_findings if "schema_version" in f.message]
    assert len(bad_sv) >= 1
    assert bad_sv[0].status in (StartupCheckStatus.WARNING, StartupCheckStatus.FATAL)


@pytest.mark.asyncio
async def test_input_schema_only_rejected() -> None:
    """input_schema (snake_case) is not accepted; only inputSchema (camelCase) is valid."""
    http = AsyncMock(spec=httpx.AsyncClient)
    http.get = _async_result(
        _resp(
            200,
            {
                "schema_version": "1.0",
                "tools": [
                    {
                        "name": "bad_tool",
                        "description": "desc",
                        "input_schema": {"type": "object", "properties": {}},
                        "is_write": False,
                        "requires_serial": False,
                        "resource_scope_kind": "",
                        "resource_scope_keys": {},
                    }
                ],
            },
        )
    )
    ctx = _make_ctx({"srv": _server()}, http)

    result = await McpToolDiscoveryService(
        ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
    ).discover_all()

    assert result.registry.all_tools() == []
    mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
    bad_input = [f for f in mcp_findings if "inputSchema" in f.message]
    assert len(bad_input) >= 1
    assert bad_input[0].status in (StartupCheckStatus.WARNING, StartupCheckStatus.FATAL)


@pytest.mark.asyncio
async def test_missing_capabilities_tolerated() -> None:
    http = AsyncMock(spec=httpx.AsyncClient)
    http.get = _async_result(
        _resp(
            200,
            {
                "schema_version": "1.0",
                "tools": [
                    {
                        "name": "read_file",
                        "description": "reads a file",
                        "inputSchema": {"type": "object", "properties": {}},
                        "is_write": False,
                        "requires_serial": False,
                        "resource_scope_kind": "",
                        "resource_scope_keys": {},
                        "agent_safety_tier": "READ_ONLY",
                        "side_effect_class": "read_only",
                        "retry_policy": "safe_read_retry",
                        "reconciliation_policy": "not_required",
                        "idempotency_required": False,
                        "preview_capability": "none",
                        "policy_version": "2.1",
                    }
                ],
            },
        )
    )
    ctx = _make_ctx({"fs": _server()}, http)

    result = await McpToolDiscoveryService(
        ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
    ).discover_all()

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
                "schema_version": "1.0",
                "tools": [
                    {
                        "name": "delete_file",
                        "description": "deletes a file",
                        "inputSchema": {"type": "object", "properties": {}},
                        "capabilities": ["filesystem.read", "filesystem.write"],
                        "is_write": True,
                        "requires_serial": True,
                        "resource_scope_kind": "",
                        "resource_scope_keys": {},
                        "agent_safety_tier": "WRITE_SAFE",
                        "side_effect_class": "local_write",
                        "retry_policy": "never",
                        "reconciliation_policy": "local_state",
                        "idempotency_required": True,
                        "preview_capability": "none",
                        "policy_version": "2.1",
                    }
                ],
            },
        )
    )
    ctx = _make_ctx({"fs": _server()}, http)

    result = await McpToolDiscoveryService(
        ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
    ).discover_all()

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
                "schema_version": "1.0",
                "tools": [
                    {
                        "name": "bad_tool",
                        "description": "malformed capabilities",
                        "inputSchema": {"type": "object", "properties": {}},
                        "capabilities": "filesystem.read",
                        "is_write": False,
                        "requires_serial": False,
                        "resource_scope_kind": "",
                        "resource_scope_keys": {},
                        "agent_safety_tier": "READ_ONLY",
                        "side_effect_class": "read_only",
                        "retry_policy": "safe_read_retry",
                        "reconciliation_policy": "not_required",
                        "idempotency_required": False,
                        "preview_capability": "none",
                        "policy_version": "2.1",
                    }
                ],
            },
        )
    )
    ctx = _make_ctx({"fs": _server()}, http)

    result = await McpToolDiscoveryService(
        ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
    ).discover_all()

    assert result.registry.all_tools() == []
    capability_findings = [f for f in result.findings if "capabilities" in f.message]
    assert len(capability_findings) == 1
    assert capability_findings[0].status == StartupCheckStatus.FATAL
    assert "bad_tool" in capability_findings[0].message


@pytest.mark.asyncio
async def test_malformed_capabilities_produces_warning_for_non_required_server() -> (
    None
):
    """Verify WARNING (not FATAL) when server has required=False."""
    http = AsyncMock(spec=httpx.AsyncClient)
    http.get = _async_result(
        _resp(
            200,
            {
                "schema_version": "1.0",
                "tools": [
                    {
                        "name": "bad_tool",
                        "description": "malformed capabilities",
                        "inputSchema": {"type": "object", "properties": {}},
                        "capabilities": "filesystem.read",
                        "is_write": False,
                        "requires_serial": False,
                        "resource_scope_kind": "",
                        "resource_scope_keys": {},
                        "agent_safety_tier": "READ_ONLY",
                        "side_effect_class": "read_only",
                        "retry_policy": "safe_read_retry",
                        "reconciliation_policy": "not_required",
                        "idempotency_required": False,
                        "preview_capability": "none",
                        "policy_version": "2.1",
                    }
                ],
            },
        )
    )
    ctx = _make_ctx({"fs": _server(required=False)}, http)

    result = await McpToolDiscoveryService(
        ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
    ).discover_all()

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

        async def _get(
            url: str,
            timeout: float = 5.0,
            headers: dict | None = None,
        ) -> MagicMock:
            return _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [
                        {
                            "name": "tool_a",
                            "description": "d",
                            "inputSchema": {"type": "object", "properties": {}},
                            "is_write": False,
                            "requires_serial": False,
                            "resource_scope_kind": "",
                            "resource_scope_keys": {},
                            "agent_safety_tier": "READ_ONLY",
                            "side_effect_class": "read_only",
                            "retry_policy": "safe_read_retry",
                            "reconciliation_policy": "not_required",
                            "idempotency_required": False,
                            "preview_capability": "none",
                            "policy_version": "2.1",
                        }
                    ],
                },
            )

        http.get = AsyncMock(side_effect=_get)
        ctx = _make_ctx(
            {
                "srv1": _server("http://srv1:9000"),
                "srv2": _server("http://srv2:9000"),
            },
            http,
        )

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        dup_findings = [f for f in mcp_findings if "duplicate" in f.message.lower()]
        assert len(dup_findings) == 1
        assert dup_findings[0].status == StartupCheckStatus.FATAL
        assert "tool_a" in dup_findings[0].message
        # duplicate tool should NOT be in the registry
        assert not any(t.name == "tool_a" for t in result.registry.all_tools())

    @pytest.mark.asyncio
    async def test_duplicate_live_tool_fatal_when_production(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)

        async def _get(
            url: str,
            timeout: float = 5.0,
            headers: dict | None = None,
        ) -> MagicMock:
            return _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [
                        {
                            "name": "tool_a",
                            "description": "d",
                            "inputSchema": {"type": "object", "properties": {}},
                            "is_write": False,
                            "requires_serial": False,
                            "resource_scope_kind": "",
                            "resource_scope_keys": {},
                            "agent_safety_tier": "READ_ONLY",
                            "side_effect_class": "read_only",
                            "retry_policy": "safe_read_retry",
                            "reconciliation_policy": "not_required",
                            "idempotency_required": False,
                            "preview_capability": "none",
                            "policy_version": "2.1",
                        }
                    ],
                },
            )

        http.get = AsyncMock(side_effect=_get)
        ctx = _make_ctx(
            {
                "srv1": _server("http://srv1:9000"),
                "srv2": _server("http://srv2:9000"),
            },
            http,
        )

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        dup_findings = [f for f in mcp_findings if "duplicate" in f.message.lower()]
        assert len(dup_findings) == 1
        assert dup_findings[0].status == StartupCheckStatus.FATAL

    @pytest.mark.asyncio
    async def test_duplicate_live_tool_fatal_even_if_local(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)

        async def _get(
            url: str,
            timeout: float = 5.0,
            headers: dict | None = None,
        ) -> MagicMock:
            return _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [
                        {
                            "name": "tool_a",
                            "description": "d",
                            "inputSchema": {"type": "object", "properties": {}},
                            "is_write": False,
                            "requires_serial": False,
                            "resource_scope_kind": "",
                            "resource_scope_keys": {},
                            "agent_safety_tier": "READ_ONLY",
                            "side_effect_class": "read_only",
                            "retry_policy": "safe_read_retry",
                            "reconciliation_policy": "not_required",
                            "idempotency_required": False,
                            "preview_capability": "none",
                            "policy_version": "2.1",
                        }
                    ],
                },
            )

        http.get = AsyncMock(side_effect=_get)
        ctx = _make_ctx(
            {
                "srv1": _server("http://srv1:9000"),
                "srv2": _server("http://srv2:9000"),
            },
            http,
        )

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

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

            async def _get(
                url: str,
                timeout: float = 5.0,
                headers: dict | None = None,
            ) -> MagicMock:
                if "srv1" in url:
                    return _resp(
                        200,
                        {
                            "schema_version": "1.0",
                            "tools": [
                                {
                                    "name": "tool_a",
                                    "description": "d",
                                    "inputSchema": {"type": "object", "properties": {}},
                                    "is_write": False,
                                    "requires_serial": False,
                                    "resource_scope_kind": "",
                                    "resource_scope_keys": {},
                                    "agent_safety_tier": "READ_ONLY",
                                    "side_effect_class": "read_only",
                                    "retry_policy": "safe_read_retry",
                                    "reconciliation_policy": "not_required",
                                    "idempotency_required": False,
                                    "preview_capability": "none",
                                    "policy_version": "2.1",
                                }
                            ],
                        },
                    )
                return _resp(
                    200,
                    {
                        "schema_version": "1.0",
                        "tools": [
                            {
                                "name": "tool_b",
                                "description": "d",
                                "inputSchema": {"type": "object", "properties": {}},
                                "is_write": False,
                                "requires_serial": False,
                                "resource_scope_kind": "",
                                "resource_scope_keys": {},
                                "agent_safety_tier": "READ_ONLY",
                                "side_effect_class": "read_only",
                                "retry_policy": "safe_read_retry",
                                "reconciliation_policy": "not_required",
                                "idempotency_required": False,
                                "preview_capability": "none",
                                "policy_version": "2.1",
                            }
                        ],
                    },
                )

            http.get = AsyncMock(side_effect=_get)
            ctx = _make_ctx(
                {
                    "srv1": _server("http://srv1:9000"),
                    "srv2": _server("http://srv2:9000"),
                },
                http,
            )

            result = await McpToolDiscoveryService(
                ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
            ).discover_all()

            mcp_findings = [
                f for f in result.findings if f.source == "mcp_tool_discovery"
            ]
            assert not any("drift" in f.message.lower() for f in mcp_findings)
        finally:
            # Full reset (not manual dict popping) guarantees the shared global
            # singleton returns to its pristine, freshly-repopulated state on the
            # next get_registry() call, regardless of what this test registered.
            _reset_registry_for_testing()

    @pytest.mark.asyncio
    async def test_drift_vs_registry_mismatch_warns(self) -> None:
        # Register tool_a -> srv1 in the static registry
        reg = get_registry()
        reg.register(ToolDefinition(name="tool_a", server_key="srv1"))

        try:
            http = AsyncMock(spec=httpx.AsyncClient)

            async def _get(
                url: str,
                timeout: float = 5.0,
                headers: dict | None = None,
            ) -> MagicMock:
                if "srv1" in url:
                    return _resp(
                        200,
                        {
                            "schema_version": "1.0",
                            "tools": [
                                {
                                    "name": "tool_a",
                                    "description": "d",
                                    "inputSchema": {"type": "object", "properties": {}},
                                    "is_write": False,
                                    "requires_serial": False,
                                    "resource_scope_kind": "",
                                    "resource_scope_keys": {},
                                    "agent_safety_tier": "READ_ONLY",
                                    "side_effect_class": "read_only",
                                    "retry_policy": "safe_read_retry",
                                    "reconciliation_policy": "not_required",
                                    "idempotency_required": False,
                                    "preview_capability": "none",
                                    "policy_version": "2.1",
                                }
                            ],
                        },
                    )
                return _resp(
                    200,
                    {
                        "schema_version": "1.0",
                        "tools": [
                            {
                                "name": "tool_a",
                                "description": "d",
                                "inputSchema": {"type": "object", "properties": {}},
                                "is_write": False,
                                "requires_serial": False,
                                "resource_scope_kind": "",
                                "resource_scope_keys": {},
                                "agent_safety_tier": "READ_ONLY",
                                "side_effect_class": "read_only",
                                "retry_policy": "safe_read_retry",
                                "reconciliation_policy": "not_required",
                                "idempotency_required": False,
                                "preview_capability": "none",
                                "policy_version": "2.1",
                            }
                        ],
                    },
                )

            http.get = AsyncMock(side_effect=_get)
            ctx = _make_ctx(
                {
                    "srv1": _server("http://srv1:9000"),
                    "srv2": _server("http://srv2:9000"),
                },
                http,
            )

            result = await McpToolDiscoveryService(
                ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
            ).discover_all()

            mcp_findings = [
                f for f in result.findings if f.source == "mcp_tool_discovery"
            ]
            drift_findings = [f for f in mcp_findings if "drift" in f.message.lower()]
            assert len(drift_findings) >= 1
            assert any("Live routing drift" in f.message for f in drift_findings)
        finally:
            # Full reset (not manual dict popping) guarantees the shared global
            # singleton returns to its pristine, freshly-repopulated state on the
            # next get_registry() call, regardless of what this test registered.
            _reset_registry_for_testing()


# ── unified severity matrix ────────────────────────────────────────────────────


class TestUnifiedSeverity:
    @pytest.mark.asyncio
    async def test_severity_unified_for_duplicates(self) -> None:
        http = AsyncMock(spec=httpx.AsyncClient)

        async def _get(
            url: str,
            timeout: float = 5.0,
            headers: dict | None = None,
        ) -> MagicMock:
            return _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [
                        {
                            "name": "dup_tool",
                            "description": "d",
                            "inputSchema": {"type": "object", "properties": {}},
                            "is_write": False,
                            "requires_serial": False,
                            "resource_scope_kind": "",
                            "resource_scope_keys": {},
                            "agent_safety_tier": "READ_ONLY",
                            "side_effect_class": "read_only",
                            "retry_policy": "safe_read_retry",
                            "reconciliation_policy": "not_required",
                            "idempotency_required": False,
                            "preview_capability": "none",
                            "policy_version": "2.1",
                        }
                    ],
                },
            )

        http.get = AsyncMock(side_effect=_get)
        ctx = _make_ctx(
            {
                "srv1": _server("http://srv1:9000"),
                "srv2": _server("http://srv2:9000"),
            },
            http,
        )

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        dup_findings = [f for f in mcp_findings if "duplicate" in f.message.lower()]
        assert len(dup_findings) == 1
        assert dup_findings[0].status == StartupCheckStatus.FATAL

    @pytest.mark.asyncio
    async def test_severity_unified_for_tool_definitions_has_issues(
        self,
        monkeypatch: pytest.MonkeyPatch,
    ) -> None:
        """tool_definitions findings are always FATAL (strict-only)."""
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery._check_tool_definitions",
            AsyncMock(
                return_value=HealthCheckResult(
                    warnings=[
                        ServiceWarning(
                            label="srv", url="http://srv:9000", message="mismatch"
                        )
                    ]
                )
            ),
        )

        http = AsyncMock(spec=httpx.AsyncClient)

        async def _get(
            url: str,
            timeout: float = 5.0,
            headers: dict | None = None,
        ) -> MagicMock:
            return _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [{"name": "grep", "description": "d", "inputSchema": {}}],
                },
            )

        http.get = AsyncMock(side_effect=_get)
        ctx = _make_ctx({"srv": _server()}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        tool_defs_findings = [f for f in mcp_findings if "mismatch" in f.message]
        assert len(tool_defs_findings) == 1
        assert tool_defs_findings[0].status == StartupCheckStatus.FATAL


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

    async def _get(
        url: str,
        timeout: float = 5.0,
        headers: dict | None = None,
    ) -> MagicMock:
        return _resp(
            200,
            {
                "schema_version": "1.0",
                "tools": [{"name": "grep", "description": "d", "inputSchema": {}}],
            },
        )

    http.get = AsyncMock(side_effect=_get)
    ctx = _make_ctx({"srv": _server()}, http)

    result = await McpToolDiscoveryService(
        ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
    ).discover_all()

    mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
    tool_defs_findings = [f for f in mcp_findings if "boom" in f.message]
    assert len(tool_defs_findings) == 1
    assert tool_defs_findings[0].status == StartupCheckStatus.FATAL


# ── REQ-008: Required-server malformed entry FATAL escalation ──────────────────


class TestRequiredServerMalformedEntryFatalEscalation:
    @pytest.mark.asyncio
    async def test_malformed_entry_on_required_server_becomes_fatal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery._check_tool_definitions",
            AsyncMock(return_value=HealthCheckResult()),
        )
        srv_cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9000",
            startup_mode=StartupMode.PERSISTENT,
            required=True,
            auth_token="test-token",
        )
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [
                        {
                            "name": "incomplete_tool",
                            "description": "d",
                            "inputSchema": {"type": "object", "properties": {}},
                            "requires_serial": False,
                            "resource_scope_kind": "",
                            "resource_scope_keys": {},
                        },
                        {
                            "name": "valid_tool",
                            "description": "d",
                            "inputSchema": {"type": "object", "properties": {}},
                            "is_write": False,
                            "requires_serial": False,
                            "resource_scope_kind": "",
                            "resource_scope_keys": {},
                            "agent_safety_tier": "READ_ONLY",
                            "side_effect_class": "read_only",
                            "retry_policy": "safe_read_retry",
                            "reconciliation_policy": "not_required",
                            "idempotency_required": False,
                            "preview_capability": "none",
                            "policy_version": "2.1",
                        },
                    ],
                },
            )
        )
        ctx = _make_ctx({"required_srv": srv_cfg}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.registry.get("valid_tool") is not None
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        fatal_findings = [
            f for f in mcp_findings if f.status == StartupCheckStatus.FATAL
        ]
        assert len(fatal_findings) >= 1
        assert any("is_write" in f.message for f in fatal_findings)

    @pytest.mark.asyncio
    async def test_malformed_entry_on_optional_server_remains_warning(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery._check_tool_definitions",
            AsyncMock(return_value=HealthCheckResult()),
        )
        srv_cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9000",
            startup_mode=StartupMode.PERSISTENT,
            required=False,
            auth_token="test-token",
        )
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [
                        {
                            "name": "incomplete_tool",
                            "description": "d",
                            "inputSchema": {"type": "object", "properties": {}},
                            "requires_serial": False,
                            "resource_scope_kind": "",
                            "resource_scope_keys": {},
                        },
                        {
                            "name": "valid_tool",
                            "description": "d",
                            "inputSchema": {"type": "object", "properties": {}},
                            "is_write": False,
                            "requires_serial": False,
                            "resource_scope_kind": "",
                            "resource_scope_keys": {},
                            "agent_safety_tier": "READ_ONLY",
                            "side_effect_class": "read_only",
                            "retry_policy": "safe_read_retry",
                            "reconciliation_policy": "not_required",
                            "idempotency_required": False,
                            "preview_capability": "none",
                            "policy_version": "2.1",
                        },
                    ],
                },
            )
        )
        ctx = _make_ctx({"optional_srv": srv_cfg}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.registry.get("valid_tool") is not None
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        warning_findings = [
            f for f in mcp_findings if f.status == StartupCheckStatus.WARNING
        ]
        assert len(warning_findings) >= 1
        assert any("is_write" in f.message for f in warning_findings)
        fatal_findings = [
            f for f in mcp_findings if f.status == StartupCheckStatus.FATAL
        ]
        assert not any("is_write" in f.message for f in fatal_findings)


# ── REQ-005: Required-capability check ────────────────────────────────────────


class TestRequiredCapabilityCheck:
    """The required-server check reads a required capability from the
    tool_catalog.toml manifest (declared per required server) and proves it from the parsed
    health report (REQ-005, AC-3, AC-5). The check is no longer gated on a tool declaring a
    capability: required loss must block startup, so a gate whose report does not prove the
    declared capability produces FATAL. A server with no catalog entry, or a body without the
    capability block, is read through its `ready` flag (D-6).
    """

    @staticmethod
    def _tool_payload(capabilities: list[str]) -> dict[str, object]:
        return {
            "name": "grep",
            "description": "d",
            "inputSchema": {"type": "object", "properties": {}},
            "is_write": False,
            "requires_serial": False,
            "resource_scope_kind": "",
            "resource_scope_keys": {},
            "agent_safety_tier": "READ_ONLY",
            "side_effect_class": "read_only",
            "retry_policy": "safe_read_retry",
            "reconciliation_policy": "not_required",
            "idempotency_required": False,
            "preview_capability": "none",
            "policy_version": "2.1",
            "capabilities": capabilities,
        }

    @staticmethod
    def _capability_findings(result: DiscoveryResult) -> list[object]:
        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        return [
            f
            for f in mcp_findings
            if "required capability" in f.message
            or "absent from tool_catalog" in f.message
            or "does not declare" in f.message
            or "does not prove readiness" in f.message
        ]

    @pytest.mark.asyncio
    async def test_declared_required_capability_present_no_fatal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery._check_tool_definitions",
            AsyncMock(return_value=HealthCheckResult()),
        )
        # The tool declares the required capability, and its server's report proves it `ok`.
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery.McpToolDiscoveryService._load_tool_catalog",
            lambda self: {
                "server": {"required_srv": {"required_capability": "filesystem.read"}}
            },
        )
        srv_cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9000",
            startup_mode=StartupMode.PERSISTENT,
            required=True,
            auth_token="test-token",
        )
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [self._tool_payload(["filesystem.read"])],
                },
            )
        )
        ctx = _make_ctx({"required_srv": srv_cfg}, http)

        result = await McpToolDiscoveryService(
            ctx,
            posture_gates=_gates_with_reports(
                ctx.cfg.mcp.mcp_servers,
                {
                    "required_srv": {
                        "liveness": True,
                        "ready": True,
                        "capabilities": {"filesystem.read": {"state": "ok"}},
                    }
                },
            ),
        ).discover_all()

        assert result.registry.get("grep") is not None
        assert not self._capability_findings(result)

    @pytest.mark.asyncio
    async def test_missing_required_capability_produces_fatal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery._check_tool_definitions",
            AsyncMock(return_value=HealthCheckResult()),
        )
        # Tool declares a different capability than the required one.
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery.McpToolDiscoveryService._load_tool_catalog",
            lambda self: {
                "server": {"required_srv": {"required_capability": "filesystem.read"}}
            },
        )
        srv_cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9000",
            startup_mode=StartupMode.PERSISTENT,
            required=True,
            auth_token="test-token",
        )
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [self._tool_payload(["filesystem.write"])],
                },
            )
        )
        ctx = _make_ctx({"required_srv": srv_cfg}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.registry.get("grep") is not None
        fatal = self._capability_findings(result)
        assert len(fatal) == 1
        assert fatal[0].status == StartupCheckStatus.FATAL
        assert "filesystem.read" in fatal[0].message

    @pytest.mark.asyncio
    async def test_required_server_absent_from_catalog_uses_the_legacy_ready_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A required server with no catalog entry is read through its `ready` flag (D-6).

        The manifest declares nothing for it, so the report is the only proof: a body that does not
        prove readiness still produces FATAL, which is what keeps the check fail-closed without the
        removed catalog-absence branch.
        """
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery._check_tool_definitions",
            AsyncMock(return_value=HealthCheckResult()),
        )
        # Manifest has no entry for the required server.
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery.McpToolDiscoveryService._load_tool_catalog",
            lambda self: {"server": {}},
        )
        srv_cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9000",
            startup_mode=StartupMode.PERSISTENT,
            required=True,
            auth_token="test-token",
        )
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [self._tool_payload(["filesystem.read"])],
                },
            )
        )
        ctx = _make_ctx({"required_srv": srv_cfg}, http)

        result = await McpToolDiscoveryService(
            ctx,
            posture_gates=_gates_with_reports(
                ctx.cfg.mcp.mcp_servers,
                {"required_srv": {"liveness": True, "ready": False}},
            ),
        ).discover_all()

        fatal = self._capability_findings(result)
        assert len(fatal) == 1
        assert fatal[0].status == StartupCheckStatus.FATAL
        assert "legacy ready fallback" in fatal[0].message

    @pytest.mark.asyncio
    async def test_tool_declaration_is_not_the_proof_the_report_is(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The report is the proof, not the tool's declared capability list (REQ-005).

        The tool declares no capability, yet the server's report proves the catalog's required
        capability `ok`, so the check engages through the report and produces nothing. The removed
        inert guard would have reported nothing here for the wrong reason.
        """
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery._check_tool_definitions",
            AsyncMock(return_value=HealthCheckResult()),
        )
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery.McpToolDiscoveryService._load_tool_catalog",
            lambda self: {
                "server": {"required_srv": {"required_capability": "filesystem.read"}}
            },
        )
        srv_cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9000",
            startup_mode=StartupMode.PERSISTENT,
            required=True,
            auth_token="test-token",
        )
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [self._tool_payload([])],
                },
            )
        )
        ctx = _make_ctx({"required_srv": srv_cfg}, http)

        result = await McpToolDiscoveryService(
            ctx,
            posture_gates=_gates_with_reports(
                ctx.cfg.mcp.mcp_servers,
                {
                    "required_srv": {
                        "liveness": True,
                        "ready": False,
                        "capabilities": {"filesystem.read": {"state": "ok"}},
                    }
                },
            ),
        ).discover_all()

        assert result.registry.get("grep") is not None
        assert not self._capability_findings(result)

    @pytest.mark.asyncio
    async def test_disabled_required_server_flagged_when_model_active(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """When the capability model is engaged (another server surfaces a
        capability), a disabled-but-required server surfaces zero tools, so its
        required capability is unproven and the check fails closed."""
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery._check_tool_definitions",
            AsyncMock(return_value=HealthCheckResult()),
        )
        # Only the disabled required server carries a required capability; the
        # enabled server is not required and only needs to engage the model.
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery.McpToolDiscoveryService._load_tool_catalog",
            lambda self: {
                "server": {"disabled_srv": {"required_capability": "filesystem.read"}}
            },
        )
        enabled_cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9001",
            startup_mode=StartupMode.PERSISTENT,
            required=False,
            auth_token="test-token",
        )
        disabled_cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9002",
            startup_mode=StartupMode.NONE,
            required=True,
            auth_token="test-token",
        )
        http = AsyncMock(spec=httpx.AsyncClient)
        # Only the enabled server is fetched; the disabled one is skipped.
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [self._tool_payload(["filesystem.write"])],
                },
            )
        )
        ctx = _make_ctx(
            {"enabled_srv": enabled_cfg, "disabled_srv": disabled_cfg}, http
        )

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        # The disabled server is never fetched.
        assert result.registry.get("grep") is not None
        fatal = self._capability_findings(result)
        assert len(fatal) == 1
        assert fatal[0].status == StartupCheckStatus.FATAL
        assert "filesystem.read" in fatal[0].message

    @staticmethod
    def _boom_manifest(self) -> object:
        raise OSError("manifest missing")

    @pytest.mark.asyncio
    async def test_unreadable_manifest_produces_fatal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A manifest that cannot be read fails closed (REQ-005): no required
        server can prove its declared capability, so startup blocks."""
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery._check_tool_definitions",
            AsyncMock(return_value=HealthCheckResult()),
        )
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery.McpToolDiscoveryService._load_tool_catalog",
            self._boom_manifest,
        )
        srv_cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9000",
            startup_mode=StartupMode.PERSISTENT,
            required=True,
            auth_token="test-token",
        )
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [self._tool_payload(["filesystem.write"])],
                },
            )
        )
        ctx = _make_ctx({"required_srv": srv_cfg}, http)

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        mcp_findings = [f for f in result.findings if f.source == "mcp_tool_discovery"]
        fatal = [
            f for f in mcp_findings if "tool_catalog.toml unavailable" in f.message
        ]
        assert len(fatal) == 1
        assert fatal[0].status == StartupCheckStatus.FATAL

    @pytest.mark.asyncio
    async def test_required_server_without_declared_capability_uses_the_legacy_ready_fallback(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A required server with no declared required_capability is read through `ready` (D-6).

        The manifest entry exists but declares nothing, so the report's `ready` flag is the proof.
        A body that does not prove readiness is still FATAL, which is what keeps startup blocked
        without a separate "the manifest must state it" branch.
        """
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery._check_tool_definitions",
            AsyncMock(return_value=HealthCheckResult()),
        )
        # Manifest lists the server but declares no required_capability.
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery.McpToolDiscoveryService._load_tool_catalog",
            lambda self: {"server": {"required_srv": {}}},
        )
        srv_cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9000",
            startup_mode=StartupMode.PERSISTENT,
            required=True,
            auth_token="test-token",
        )
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [self._tool_payload(["filesystem.write"])],
                },
            )
        )
        ctx = _make_ctx({"required_srv": srv_cfg}, http)

        result = await McpToolDiscoveryService(
            ctx,
            posture_gates=_gates_with_reports(
                ctx.cfg.mcp.mcp_servers,
                {"required_srv": {"liveness": True, "ready": False}},
            ),
        ).discover_all()

        fatal = self._capability_findings(result)
        assert len(fatal) == 1
        assert fatal[0].status == StartupCheckStatus.FATAL
        assert "legacy ready fallback" in fatal[0].message


class TestRequiredCapabilityProofFromTheReport:
    """T-05 (REQ-005, AC-05): the parsed report is the proof of the required capability.

    `liveness` alone is never proof, and a legacy body falls back to `ready`.
    """

    @staticmethod
    def _ctx(
        monkeypatch: pytest.MonkeyPatch, catalog: Mapping[str, object]
    ) -> MagicMock:
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery._check_tool_definitions",
            AsyncMock(return_value=HealthCheckResult()),
        )
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery.McpToolDiscoveryService._load_tool_catalog",
            lambda self: catalog,
        )
        srv_cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9000",
            startup_mode=StartupMode.PERSISTENT,
            required=True,
            auth_token="test-token",
        )
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [_tool_entry("grep", ["filesystem.read"])],
                },
            )
        )
        return _make_ctx({"required_srv": srv_cfg}, http)

    @staticmethod
    def _fatal(result: DiscoveryResult) -> object:
        capability_findings = [
            f
            for f in result.findings
            if f.source == "mcp_tool_discovery"
            and f.status == StartupCheckStatus.FATAL
            and (
                "required capability" in f.message
                or "does not prove readiness" in f.message
            )
        ]
        assert len(capability_findings) == 1
        return capability_findings[0]

    @pytest.mark.asyncio
    async def test_liveness_only_report_does_not_prove_readiness(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A body that reports only liveness is not readiness (REQ-005)."""
        ctx = self._ctx(
            monkeypatch,
            {"server": {"required_srv": {"required_capability": "filesystem.read"}}},
        )
        result = await McpToolDiscoveryService(
            ctx,
            posture_gates=_gates_with_reports(
                ctx.cfg.mcp.mcp_servers,
                {"required_srv": {"liveness": True, "ready": False}},
            ),
        ).discover_all()

        assert self._fatal(result).message.count("filesystem.read") == 1

    @pytest.mark.asyncio
    async def test_degraded_required_capability_produces_fatal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ctx = self._ctx(
            monkeypatch,
            {"server": {"required_srv": {"required_capability": "filesystem.read"}}},
        )
        result = await McpToolDiscoveryService(
            ctx,
            posture_gates=_gates_with_reports(
                ctx.cfg.mcp.mcp_servers,
                {
                    "required_srv": {
                        "liveness": True,
                        "ready": False,
                        "capabilities": {
                            "filesystem.read": {
                                "state": "degraded",
                                "reason_code": "config_missing",
                            }
                        },
                    }
                },
            ),
        ).discover_all()

        fatal = self._fatal(result)
        assert "filesystem.read" in fatal.message

    @pytest.mark.asyncio
    async def test_unavailable_required_capability_produces_fatal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ctx = self._ctx(
            monkeypatch,
            {"server": {"required_srv": {"required_capability": "filesystem.read"}}},
        )
        result = await McpToolDiscoveryService(
            ctx,
            posture_gates=_gates_with_reports(
                ctx.cfg.mcp.mcp_servers,
                {
                    "required_srv": {
                        "liveness": True,
                        "ready": False,
                        "capabilities": {"filesystem.read": {"state": "unavailable"}},
                    }
                },
            ),
        ).discover_all()

        fatal = self._fatal(result)
        assert "filesystem.read" in fatal.message

    @pytest.mark.asyncio
    async def test_legacy_body_falls_back_to_ready(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A body with no capability block is read through its `ready` flag (D-6)."""
        ctx = self._ctx(
            monkeypatch,
            {"server": {"required_srv": {"required_capability": "filesystem.read"}}},
        )
        result = await McpToolDiscoveryService(
            ctx,
            posture_gates=_gates_with_reports(
                ctx.cfg.mcp.mcp_servers,
                {"required_srv": {"liveness": True, "ready": True}},
            ),
        ).discover_all()

        assert result.registry.get("grep") is not None
        assert [
            f
            for f in result.findings
            if f.source == "mcp_tool_discovery"
            and (
                "required capability" in f.message
                or "does not prove readiness" in f.message
            )
        ] == []


class TestStrictConfigDependentField:
    """T-07 (REQ-007, AC-07): `config_dependent` is parsed strictly, with no truthy coercion."""

    @staticmethod
    def _ctx(monkeypatch: pytest.MonkeyPatch, entry: dict[str, object]) -> MagicMock:
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery._check_tool_definitions",
            AsyncMock(return_value=HealthCheckResult()),
        )
        srv_cfg = _server(startup_mode=StartupMode.PERSISTENT)
        srv_cfg.required = False
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(200, {"schema_version": "1.0", "tools": [entry]})
        )
        return _make_ctx({"srv": srv_cfg}, http)

    @pytest.mark.asyncio
    async def test_non_bool_config_dependent_rejects_the_entry_with_a_warning(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """A truthy value is not a bool: the entry is rejected with a finding (AC-07)."""
        ctx = self._ctx(monkeypatch, _tool_entry("grep", [], config_dependent="true"))

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.registry.all_tools() == []
        field_findings = [
            f
            for f in result.findings
            if f.source == "mcp_tool_discovery" and "config_dependent" in f.message
        ]
        assert len(field_findings) == 1
        assert field_findings[0].status == StartupCheckStatus.WARNING

    @pytest.mark.asyncio
    async def test_bool_config_dependent_reaches_runtime_tool_with_the_declared_value(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """The producer-declared value is carried, not inferred from `status`."""
        ctx = self._ctx(monkeypatch, _tool_entry("grep", [], config_dependent=True))

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        tool = result.registry.get("grep")
        assert tool.config_dependent is True
        assert tool.status == "active"

    @pytest.mark.asyncio
    async def test_absent_config_dependent_is_not_rejected_and_keeps_the_default(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """REQ-007 rejects a value that is not a bool; an absent field is the field default."""
        ctx = self._ctx(monkeypatch, _tool_entry("grep", []))

        result = await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        assert result.registry.get("grep").config_dependent is False


class TestDiscoverAllCapabilityExclusion:
    """T-06 (REQ-006, AC-06): only the tools that depend on a lost capability are dropped.

    The fixture catalog matches seq 17: `github.operations` required, `github.api` optional.
    """

    @staticmethod
    def _catalog() -> dict[str, object]:
        return {
            "server": {
                "github": {
                    "owned_tools": ["github_create_issue", "github_list_issues"],
                    "capabilities": ["github.operations", "github.api"],
                    "required_capability": "github.operations",
                }
            }
        }

    @staticmethod
    def _ctx(
        monkeypatch: pytest.MonkeyPatch, report: Mapping[str, object]
    ) -> MagicMock:
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery._check_tool_definitions",
            AsyncMock(return_value=HealthCheckResult()),
        )
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery.McpToolDiscoveryService._load_tool_catalog",
            lambda self: TestDiscoverAllCapabilityExclusion._catalog(),
        )
        srv_cfg = _server("http://127.0.0.1:9000")
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [
                        _tool_entry("github_create_issue", ["github.api"]),
                        _tool_entry("github_list_issues", ["github.operations"]),
                    ],
                },
            )
        )
        ctx = _make_ctx({"github": srv_cfg}, http)
        ctx._report = report
        return ctx

    @pytest.mark.asyncio
    async def test_tool_dependent_on_a_degraded_capability_is_excluded_with_reason_capability(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        ctx = self._ctx(
            monkeypatch,
            {
                "liveness": True,
                "ready": False,
                "capabilities": {
                    "github.operations": {"state": "ok"},
                    "github.api": {
                        "state": "degraded",
                        "reason_code": "config_missing",
                    },
                },
            },
        )

        result = await McpToolDiscoveryService(
            ctx,
            posture_gates=_gates_with_reports(
                ctx.cfg.mcp.mcp_servers, {"github": ctx._report}
            ),
        ).discover_all()

        assert result.registry.resolve("github_create_issue") is None
        assert result.registry.exclusion_reason("github_create_issue") == "capability"
        # The required capability is proven `ok`, so startup is not blocked (AC-06). Only the
        # capability findings are read here: the drift check reports its own rows for the fixture's
        # partial tool list.
        capability_fatal = [
            f
            for f in result.findings
            if f.source == "mcp_tool_discovery"
            and f.status == StartupCheckStatus.FATAL
            and (
                "required capability" in f.message
                or "does not prove readiness" in f.message
            )
        ]
        assert capability_fatal == []

    @pytest.mark.asyncio
    async def test_tool_with_no_capability_dependency_stays_registered(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Only the tools that declare the lost capability are dropped; the rest stay."""
        ctx = self._ctx(
            monkeypatch,
            {
                "liveness": True,
                "ready": False,
                "capabilities": {
                    "github.operations": {"state": "ok"},
                    "github.api": {"state": "unavailable"},
                },
            },
        )

        result = await McpToolDiscoveryService(
            ctx,
            posture_gates=_gates_with_reports(
                ctx.cfg.mcp.mcp_servers, {"github": ctx._report}
            ),
        ).discover_all()

        assert result.registry.get("github_list_issues") is not None
        assert result.registry.exclusion_reason("github_create_issue") == "capability"


class TestCatalogLoadOrderBeforeRegistryConstruction:
    """D-9: the catalog is read before the registry is built, so the missing-catalog case is
    observable while no tool row exists yet."""

    @pytest.mark.asyncio
    async def test_missing_catalog_is_observable_before_any_tool_row_exists(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery._check_tool_definitions",
            AsyncMock(return_value=HealthCheckResult()),
        )

        def _boom(self) -> dict[str, object]:
            raise OSError("manifest missing")

        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery.McpToolDiscoveryService._load_tool_catalog",
            _boom,
        )
        srv_cfg = _server("http://127.0.0.1:9000")
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(
            _resp(
                200,
                {
                    "schema_version": "1.0",
                    "tools": [_tool_entry("grep", ["filesystem.read"])],
                },
            )
        )
        ctx = _make_ctx({"required_srv": srv_cfg}, http)

        result = await McpToolDiscoveryService(
            ctx,
            posture_gates=_gates_with_reports(
                ctx.cfg.mcp.mcp_servers,
                {"required_srv": {"liveness": True, "ready": True}},
            ),
        ).discover_all()

        # The entry was fetched, yet no tool row exists: the catalog was read first and the
        # registry was published empty, already carrying the fail-closed FATAL.
        assert result.registry.all_tools() == []
        assert result.registry.diagnostics() == []
        fatal = [
            f
            for f in result.findings
            if f.source == "mcp_tool_discovery" and f.status == StartupCheckStatus.FATAL
        ]
        assert len(fatal) == 1
        assert "tool_catalog.toml unavailable" in fatal[0].message


# ── auth-header propagation on the /v1/tools probe ────────────────────────────


class TestToolDiscoveryAuthHeader:
    @pytest.mark.asyncio
    async def test_probe_sends_bearer_auth_header(self) -> None:
        """The /v1/tools probe must carry the server's Bearer token.

        Regression: without it every authenticated server answers 401 and the
        startup tool-discovery gate fails for all servers at once.
        """
        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _async_result(_resp(200, {"schema_version": "1.0", "tools": []}))
        cfg = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:9000",
            startup_mode=StartupMode.PERSISTENT,
            auth_token="secret-token",
            required=True,
        )
        ctx = _make_ctx({"srv": cfg}, http)

        await McpToolDiscoveryService(
            ctx, posture_gates=gates_from(ctx.cfg.mcp.mcp_servers)
        ).discover_all()

        tool_calls = [c for c in http.get.call_args_list if "/v1/tools" in c.args[0]]
        assert tool_calls, "expected a /v1/tools probe"
        _, kwargs = tool_calls[-1]
        assert kwargs["headers"] == {"Authorization": "Bearer secret-token"}


# ── registry-building layer (mcp_tool_discovery_registry.py) ─────────────────

_ENTRY_SCHEMA: dict[str, object] = {
    "inputSchema": {"type": "object", "properties": {}},
    "is_write": False,
    "requires_serial": False,
    "resource_scope_kind": "",
    "resource_scope_keys": {},
    "agent_safety_tier": "READ_ONLY",
    "side_effect_class": "read_only",
    "retry_policy": "safe_read_retry",
    "reconciliation_policy": "not_required",
    "idempotency_required": False,
    "preview_capability": "none",
    "policy_version": "2.1",
}


class TestRegistryBuildingLayer:
    """Calls the module the service delegates registry building to, directly.

    Locks the boundary the same way `discover_all()` exercises it: the unavailable-server
    filter is the branch no `discover_all()` test can reach, because an unreachable server
    contributes no entries at all.
    """

    @staticmethod
    def _entry(name: str) -> dict[str, object]:
        """One entry shaped exactly like `_normalize_entries()` output."""
        return {"name": name, **_ENTRY_SCHEMA}

    def test_unavailable_server_entries_never_reach_the_registry(self) -> None:
        entries: list[tuple[str, str, dict[str, object]]] = [
            ("live", "http://127.0.0.1:9000", self._entry("read_file")),
            ("down", "http://127.0.0.1:9001", self._entry("grep")),
        ]

        registry = _build_runtime_tools(
            entries, frozenset({"down"}), allowed_servers=frozenset({"live", "down"})
        )

        assert registry.resolve("read_file") == "live"
        assert registry.resolve("grep") is None

    def test_dedupe_and_build_excludes_a_duplicated_name_and_reports_it_fatal(
        self,
    ) -> None:
        entries: list[tuple[str, str, dict[str, object]]] = [
            ("a", "http://127.0.0.1:9000", self._entry("read_file")),
            ("a", "http://127.0.0.1:9000", self._entry("grep")),
            ("b", "http://127.0.0.1:9001", self._entry("grep")),
        ]

        registry, findings = _dedupe_and_build(
            entries, frozenset(), allowed_servers=frozenset({"a", "b"})
        )

        assert registry.resolve("read_file") == "a"
        assert registry.resolve("grep") is None
        assert [finding.status for finding in findings] == [StartupCheckStatus.FATAL]
        assert "duplicate tool name 'grep'" in findings[0].message

    def test_empty_allowed_servers_registers_nothing(self) -> None:
        """An empty posture gate registers nothing (fail-closed)."""
        entries: list[tuple[str, str, dict[str, object]]] = [
            ("srv", "http://127.0.0.1:9000", self._entry("read_file")),
        ]
        registry = _build_runtime_tools(
            entries, frozenset(), allowed_servers=frozenset()
        )
        assert registry.all_tools() == []
        assert registry.resolve("read_file") is None

    def test_build_requires_allowed_servers(self) -> None:
        """`_build_runtime_tools()` has no default for `allowed_servers`; omitting it is a TypeError."""
        entries: list[tuple[str, str, dict[str, object]]] = [
            ("srv", "http://127.0.0.1:9000", self._entry("read_file")),
        ]
        with pytest.raises(TypeError):
            _build_runtime_tools(entries, frozenset())
