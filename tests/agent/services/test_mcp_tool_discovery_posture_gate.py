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
from agent.services.mcp_tool_discovery import DiscoveryResult, McpToolDiscoveryService
from agent.shared.health_models import StartupCheckOutcome, StartupCheckStatus
from shared.mcp_config import McpServerConfig, StartupMode, TransportType
from shared.mcp_health_contract import HealthReport, parse_health_body
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
    """Build a schema-2.1 /v1/tools body carrying one complete entry per name."""
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
                "resource_scope_keys": {},
                "agent_safety_tier": "READ_ONLY",
                "side_effect_class": "read_only",
                "retry_policy": "safe_read_retry",
                "reconciliation_policy": "not_required",
                "idempotency_required": False,
                "preview_capability": "none",
                "policy_version": "2.1",
            }
            for name in names
        ],
    }


def _server(
    url: str = "http://127.0.0.1:9000",
    required: bool = True,
) -> McpServerConfig:
    return McpServerConfig(
        transport=TransportType.HTTP,
        url=url,
        startup_mode=StartupMode.PERSISTENT,
        auth_token="test-token",
        required=required,
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


def _report(**body: object) -> HealthReport:
    """Parse a `/health` body through the shared contract, the shape a gate carries."""
    return parse_health_body(body)


def _catalog(server_key: str, required_capability: str) -> dict[str, object]:
    """A catalog fixture for one server, so the test does not read config/tool_catalog.toml."""
    return {"server": {server_key: {"required_capability": required_capability}}}


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


class TestRequiredCapabilityProofFromTheGateReport:
    """T-05 (REQ-005/AC-05): the report the gate carries is the proof and the catalog
    supplies the identifier. The tool-declaration guard is gone, so the check engages
    for every required server.
    """

    @staticmethod
    def _capability_findings(result: DiscoveryResult) -> list[StartupCheckOutcome]:
        return [
            f
            for f in result.findings
            if f.source == _SOURCE and "required capability" in f.message
        ]

    @pytest.mark.asyncio
    async def test_degraded_required_capability_produces_fatal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        http = _http(
            {"http://127.0.0.1:9000/v1/tools": _tools_body("github_list_issues")}
        )
        ctx = _make_ctx({"github": _server()}, http)
        report = _report(
            health_schema_version=1,
            liveness=True,
            ready=False,
            capabilities={
                "github.operations": {
                    "state": "degraded",
                    "reason_code": "server_unavailable",
                }
            },
        )
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery.McpToolDiscoveryService._load_tool_catalog",
            lambda self: _catalog("github", "github.operations"),
        )
        gates = {"github": replace(_gate("github"), report=report)}

        result = await McpToolDiscoveryService(ctx, posture_gates=gates).discover_all()

        fatal = self._capability_findings(result)
        assert len(fatal) == 1
        assert fatal[0].status == StartupCheckStatus.FATAL
        assert "github.operations" in fatal[0].message

    @pytest.mark.asyncio
    async def test_unavailable_required_capability_produces_fatal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        http = _http(
            {"http://127.0.0.1:9000/v1/tools": _tools_body("github_list_issues")}
        )
        ctx = _make_ctx({"github": _server()}, http)
        report = _report(
            health_schema_version=1,
            liveness=True,
            ready=False,
            capabilities={
                "github.operations": {
                    "state": "unavailable",
                    "reason_code": "config_missing",
                }
            },
        )
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery.McpToolDiscoveryService._load_tool_catalog",
            lambda self: _catalog("github", "github.operations"),
        )
        gates = {"github": replace(_gate("github"), report=report)}

        result = await McpToolDiscoveryService(ctx, posture_gates=gates).discover_all()

        fatal = self._capability_findings(result)
        assert len(fatal) == 1
        assert fatal[0].status == StartupCheckStatus.FATAL

    @pytest.mark.asyncio
    async def test_proven_required_capability_reports_nothing(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        http = _http(
            {"http://127.0.0.1:9000/v1/tools": _tools_body("github_list_issues")}
        )
        ctx = _make_ctx({"github": _server()}, http)
        report = _report(
            health_schema_version=1,
            liveness=True,
            ready=False,
            capabilities={"github.operations": {"state": "ok"}},
        )
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery.McpToolDiscoveryService._load_tool_catalog",
            lambda self: _catalog("github", "github.operations"),
        )
        gates = {"github": replace(_gate("github"), report=report)}

        result = await McpToolDiscoveryService(ctx, posture_gates=gates).discover_all()

        assert not self._capability_findings(result)
        assert _tool_names(result.registry) == {"github_list_issues"}

    @pytest.mark.asyncio
    async def test_legacy_body_falls_back_to_ready(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """D-6: a body with no capability block is read through its `ready` flag."""
        http = _http(
            {"http://127.0.0.1:9000/v1/tools": _tools_body("github_list_issues")}
        )
        ctx = _make_ctx({"github": _server()}, http)
        report = _report(health_schema_version=0, liveness=True, ready=True)
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery.McpToolDiscoveryService._load_tool_catalog",
            lambda self: _catalog("github", "github.operations"),
        )
        gates = {"github": replace(_gate("github"), report=report)}

        result = await McpToolDiscoveryService(ctx, posture_gates=gates).discover_all()

        assert not self._capability_findings(result)

    @pytest.mark.asyncio
    async def test_legacy_body_not_ready_produces_fatal(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        http = _http(
            {"http://127.0.0.1:9000/v1/tools": _tools_body("github_list_issues")}
        )
        ctx = _make_ctx({"github": _server()}, http)
        report = _report(health_schema_version=0, liveness=True, ready=False)
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery.McpToolDiscoveryService._load_tool_catalog",
            lambda self: _catalog("github", "github.operations"),
        )
        gates = {"github": replace(_gate("github"), report=report)}

        result = await McpToolDiscoveryService(ctx, posture_gates=gates).discover_all()

        fatal = self._capability_findings(result)
        assert len(fatal) == 1
        assert fatal[0].status == StartupCheckStatus.FATAL

    @pytest.mark.asyncio
    async def test_optional_degraded_capability_produces_the_map(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """T-05 (REQ-006): the optional loss is collected per server for the registry; the
        exclusion itself is the registry's decision (seq 13), so the tool is still built here.
        """
        http = _http(
            {"http://127.0.0.1:9000/v1/tools": _tools_body("github_list_issues")}
        )
        ctx = _make_ctx({"github": _server()}, http)
        report = _report(
            health_schema_version=1,
            liveness=True,
            ready=True,
            capabilities={
                "github.operations": {"state": "ok"},
                "github.api": {"state": "degraded", "reason_code": "config_missing"},
            },
        )
        catalog = {
            "server": {
                "github": {
                    "required_capability": "github.operations",
                    "capabilities": ["github.operations", "github.api"],
                }
            }
        }
        monkeypatch.setattr(
            "agent.services.mcp_tool_discovery.McpToolDiscoveryService._load_tool_catalog",
            lambda self: catalog,
        )
        gates = {"github": replace(_gate("github"), report=report)}

        service = McpToolDiscoveryService(ctx, posture_gates=gates)
        result = await service.discover_all()

        assert not self._capability_findings(result)
        assert service._degraded_capability_map(catalog) == {"github": ("github.api",)}
