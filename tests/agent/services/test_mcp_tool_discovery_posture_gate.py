"""tests/agent/services/test_mcp_tool_discovery_posture_gate.py
Unit tests for the Security Posture gate in McpToolDiscoveryService: gates arrive from the caller,
are reduced to a server-key allowlist, and reach RuntimeToolRegistry unchanged.
"""

from __future__ import annotations

from dataclasses import replace
from unittest.mock import AsyncMock, MagicMock

import httpx
import pytest
from agent.services.mcp_health import PostureGate, classify_server_failure
from agent.services.mcp_tool_discovery import McpToolDiscoveryService
from agent.shared.health_models import StartupCheckStatus
from shared.mcp_config import McpServerConfig, StartupMode, TransportType
from shared.runtime_tool_registry import RuntimeToolRegistry
from shared.security.result_dto import REASON_OK, REASON_POSTURE_MISSING

_SOURCE = "mcp_tool_discovery"


def _resp(status_code: int = 200, json_value: object = None) -> MagicMock:
    """Build a MagicMock standing in for an httpx.Response."""
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = json_value
    return resp


def _tools_body(*names: str) -> dict[str, object]:
    """Build a schema-2.0 /v1/tools body carrying one entry per name."""
    return {
        "schema_version": "1.0",
        "tools": [
            {
                "name": name,
                "description": name,
                "inputSchema": {"type": "object", "properties": {}},
                "is_write": False,
                "requires_serial": False,
                "resource_scope_kind": "",
                "resource_scope_keys": [],
            }
            for name in names
        ],
    }


def _server(
    url: str = "http://127.0.0.1:9000",
    required: bool = True,
    tool_names: list[str] | None = None,
) -> McpServerConfig:
    return McpServerConfig(
        transport=TransportType.HTTP,
        url=url,
        startup_mode=StartupMode.PERSISTENT,
        auth_token="test-token",
        required=required,
        tool_names=list(tool_names or []),
    )


def _http(bodies: dict[str, dict[str, object]]) -> AsyncMock:
    """AsyncClient double answering each server URL with its own tool body."""

    async def _get(url: str, **kwargs: object) -> MagicMock:
        if url not in bodies:
            raise httpx.ConnectError(f"no route to {url}")
        return _resp(200, bodies[url])

    http = AsyncMock(spec=httpx.AsyncClient)
    http.get = _get
    return http


def _make_ctx(servers: dict[str, McpServerConfig], http: AsyncMock) -> MagicMock:
    ctx = MagicMock()
    ctx.cfg.mcp.mcp_servers = servers
    ctx.cfg.tool.tool_definitions_strict = False
    ctx.services_required.http = http
    return ctx


def _gate(
    server_key: str,
    *,
    reachable: bool = True,
    posture_accepted: bool = True,
    ready: bool = True,
    validated: bool = True,
    required: bool = True,
) -> PostureGate:
    """Build one gate and attach the failure class the row 18 classifier would attach."""
    gate = PostureGate(
        server_key=server_key,
        required=required,
        reachable=reachable,
        posture_accepted=posture_accepted,
        ready=ready,
        validated=validated,
        reason_code=REASON_OK if posture_accepted else REASON_POSTURE_MISSING,
    )
    return replace(gate, failure_class=classify_server_failure(gate))


def _tool_names(registry: RuntimeToolRegistry) -> set[str]:
    return {tool.name for tool in registry.all_tools()}


class TestPostureGateReachesTheRegistry:
    @pytest.mark.asyncio
    async def test_a_server_with_a_non_green_gate_contributes_no_tool(self) -> None:
        http = _http({"http://127.0.0.1:9000/v1/tools": _tools_body("git_push")})
        ctx = _make_ctx({"git": _server()}, http)
        gates = {
            "git": _gate("git", posture_accepted=False, ready=False, validated=False)
        }

        result = await McpToolDiscoveryService(ctx, posture_gates=gates).discover_all()

        assert _tool_names(result.registry) == set()
        assert result.registry.posture_excluded_servers == frozenset({"git"})

    @pytest.mark.asyncio
    async def test_a_green_gate_keeps_the_tool(self) -> None:
        http = _http({"http://127.0.0.1:9000/v1/tools": _tools_body("mdq_query")})
        ctx = _make_ctx({"mdq": _server()}, http)
        gates = {"mdq": _gate("mdq")}

        result = await McpToolDiscoveryService(ctx, posture_gates=gates).discover_all()

        assert _tool_names(result.registry) == {"mdq_query"}
        assert result.registry.posture_excluded_servers == frozenset()

    def test_no_gate_supplied_raises_typeerror(self) -> None:
        """The required-argument contract: construction without gates fails at once."""
        http = _http({"http://127.0.0.1:9000/v1/tools": _tools_body("git_push")})
        ctx = _make_ctx({"git": _server()}, http)

        with pytest.raises(TypeError):
            McpToolDiscoveryService(ctx)

    @pytest.mark.asyncio
    async def test_an_empty_gate_registers_no_mcp_tool(self) -> None:
        """The fail-closed reading: a supplied gate with no green member allows nothing."""
        http = _http({"http://127.0.0.1:9000/v1/tools": _tools_body("git_push")})
        ctx = _make_ctx({"git": _server()}, http)

        result = await McpToolDiscoveryService(ctx, posture_gates={}).discover_all()

        assert _tool_names(result.registry) == set()
        assert result.registry.posture_excluded_servers == frozenset({"git"})

    @pytest.mark.asyncio
    async def test_only_the_gated_server_loses_its_tool(self) -> None:
        bodies = {
            "http://127.0.0.1:9000/v1/tools": _tools_body("git_push"),
            "http://127.0.0.1:9001/v1/tools": _tools_body("mdq_query"),
        }
        ctx = _make_ctx(
            {
                "git": _server("http://127.0.0.1:9000"),
                "mdq": _server("http://127.0.0.1:9001"),
            },
            _http(bodies),
        )
        gates = {
            "git": _gate("git", validated=False),
            "mdq": _gate("mdq"),
        }

        result = await McpToolDiscoveryService(ctx, posture_gates=gates).discover_all()

        assert _tool_names(result.registry) == {"mdq_query"}
        assert result.registry.posture_excluded_servers == frozenset({"git"})


class TestPostureGateIsNotAvailability:
    @pytest.mark.asyncio
    async def test_a_posture_rejected_server_is_not_reported_as_unreachable(
        self,
    ) -> None:
        """A server that answers but whose posture failed is a posture exclusion, not an outage."""
        bodies = {
            "http://127.0.0.1:9000/v1/tools": _tools_body("git_push"),
            "http://127.0.0.1:9001/v1/tools": _tools_body("mdq_query"),
        }
        ctx = _make_ctx(
            {
                "git": _server("http://127.0.0.1:9000"),
                "mdq": _server("http://127.0.0.1:9001"),
            },
            _http(bodies),
        )
        gates = {
            "git": _gate("git", posture_accepted=False, ready=False, validated=False),
            "mdq": _gate("mdq"),
        }

        result = await McpToolDiscoveryService(ctx, posture_gates=gates).discover_all()

        assert result.unreachable == []
        assert _tool_names(result.registry) == {"mdq_query"}
        assert result.registry.posture_excluded_servers == frozenset({"git"})

    @pytest.mark.asyncio
    async def test_availability_and_posture_exclusions_stay_in_separate_reports(
        self,
    ) -> None:
        # git never answers and is absent from the gate; mdq answers but its posture failed.
        bodies = {"http://127.0.0.1:9001/v1/tools": _tools_body("mdq_query")}
        ctx = _make_ctx(
            {
                "git": _server("http://127.0.0.1:9000"),
                "mdq": _server("http://127.0.0.1:9001"),
            },
            _http(bodies),
        )
        gates = {"mdq": _gate("mdq", validated=False)}

        result = await McpToolDiscoveryService(ctx, posture_gates=gates).discover_all()

        assert result.unreachable == ["git"]
        assert _tool_names(result.registry) == set()
        assert result.registry.posture_excluded_servers == frozenset({"mdq"})


class TestPostureGateDoesNotProbeHealth:
    @pytest.mark.asyncio
    async def test_the_gate_adds_no_health_probe(self) -> None:
        called: list[str] = []
        bodies = {"http://127.0.0.1:9000/v1/tools": _tools_body("git_push")}

        async def _get(url: str, **kwargs: object) -> MagicMock:
            called.append(url)
            return _resp(200, bodies[url])

        http = AsyncMock(spec=httpx.AsyncClient)
        http.get = _get
        ctx = _make_ctx({"git": _server()}, http)
        gates = {
            "git": _gate("git", posture_accepted=False, ready=False, validated=False)
        }

        result = await McpToolDiscoveryService(ctx, posture_gates=gates).discover_all()

        assert set(called) == {"http://127.0.0.1:9000/v1/tools"}
        assert all(url.endswith("/v1/tools") for url in called)
        assert _tool_names(result.registry) == set()

    @pytest.mark.asyncio
    async def test_a_gated_server_is_still_fetched_before_being_excluded(self) -> None:
        """The gate is applied at registry construction, so drift findings keep their input."""
        http = _http({"http://127.0.0.1:9000/v1/tools": _tools_body("git_push")})
        ctx = _make_ctx({"git": _server()}, http)
        gates = {
            "git": _gate("git", posture_accepted=False, ready=False, validated=False)
        }

        result = await McpToolDiscoveryService(ctx, posture_gates=gates).discover_all()

        assert result.unreachable == []
        assert _tool_names(result.registry) == set()


class TestRequiredToolInteraction:
    @pytest.mark.asyncio
    async def test_a_required_tool_of_a_posture_rejected_server_is_a_fatal_finding(
        self,
    ) -> None:
        http = _http({"http://127.0.0.1:9000/v1/tools": _tools_body("git_push")})
        ctx = _make_ctx({"git": _server(tool_names=["git_push"])}, http)
        gates = {
            "git": _gate("git", posture_accepted=False, ready=False, validated=False)
        }

        result = await McpToolDiscoveryService(ctx, posture_gates=gates).discover_all()

        missing = [
            finding
            for finding in result.findings
            if finding.source == _SOURCE and "git_push" in finding.message
        ]
        assert len(missing) == 1
        assert missing[0].status == StartupCheckStatus.FATAL

    @pytest.mark.asyncio
    async def test_a_green_gate_keeps_the_required_tool_present(self) -> None:
        http = _http({"http://127.0.0.1:9000/v1/tools": _tools_body("git_push")})
        ctx = _make_ctx({"git": _server(tool_names=["git_push"])}, http)
        gates = {"git": _gate("git")}

        result = await McpToolDiscoveryService(ctx, posture_gates=gates).discover_all()

        assert not [
            finding
            for finding in result.findings
            if finding.source == _SOURCE
            and "not found in discovery results" in finding.message
        ]
