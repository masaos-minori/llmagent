"""tests/agent/test_mcp_health_posture.py

Tests for the MCP Security Posture gating in scripts/agent/services/mcp_health.py:
collect_server_postures() probes every usable HTTP server once and turns the answer into a gate,
classify_server_failure() separates Availability from Safety and Integrity, allowed_server_keys()
keeps only fully green gates, check_service_health() routes a required server's failure and any Safety
or Integrity posture failure into errors, and check_readiness() aborts startup on a Safety or Integrity
failure without copying a fingerprint or a server-supplied message into the Agent's message.
"""

from __future__ import annotations

import time
from typing import Any
from unittest.mock import MagicMock

import httpx
import pytest
from agent.commands.cmd_mcp import _format_availability_display
from agent.output_tags import OutputTag
from agent.services.enums import McpAvailability, McpTier
from agent.services.mcp_health import (
    PostureGate,
    ServerFailureClass,
    allowed_server_keys,
    check_readiness,
    check_service_health,
    classify_server_failure,
    collect_server_postures,
)
from agent.services.models import McpProbeResult
from shared.mcp_config import McpServerConfig, StartupMode, TransportType
from shared.mcp_health import McpServerHealthRegistry, McpServerHealthState
from shared.security.posture_contract import (
    REQUIRED_CHECK_IDS,
    SECURITY_CONTRACT_VERSION,
)
from shared.security.result_dto import (
    REASON_AUTH_TOKEN_MISSING,
    REASON_CHECK_SET_MISMATCH,
    REASON_CONFIG_INVALID,
    REASON_CONTRACT_VERSION_MISMATCH,
    REASON_DEPENDENCY_UNREACHABLE,
    REASON_OK,
    REASON_POSTURE_MISSING,
    REASON_SERVER_KEY_MISMATCH,
)

SERVER_KEY = "mdq"
FINGERPRINT = "a" * 64
SECRET_TEXT = "/opt/llm/secret/token-value"
BASE_URL = "http://mdq-mcp:8091"
HEALTH_URL = f"{BASE_URL}/health"


def _server(
    url: str = BASE_URL,
    *,
    required: bool = True,
    startup_mode: StartupMode = StartupMode.PERSISTENT,
    auth_token: str = "test-token",
) -> McpServerConfig:
    """One configured MCP server, persistent so no cmd is required."""
    return McpServerConfig(
        transport=TransportType.HTTP,
        url=url,
        startup_mode=startup_mode,
        required=required,
        auth_token=auth_token,
        tool_names=["probe"],
    )


def _fake_cfg(**overrides: Any) -> MagicMock:
    """A server config that cannot be built as a real one, to prove a skip rule."""
    cfg = MagicMock()
    cfg.transport = TransportType.HTTP
    cfg.url = BASE_URL
    cfg.is_disabled = False
    cfg.required = True
    cfg.auth_headers.return_value = {}
    for name, value in overrides.items():
        setattr(cfg, name, value)
    return cfg


class _Probe:
    """Stands in for the shared httpx client: records every request, serves a canned answer."""

    def __init__(self, responses: dict[str, Any]) -> None:
        self.responses = responses
        self.calls: list[tuple[str, dict[str, Any]]] = []

    async def get(self, url: str, **kwargs: Any) -> Any:
        self.calls.append((url, kwargs))
        outcome = self.responses[url]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome


def _http(responses: dict[str, Any]) -> _Probe:
    """Serve each /health URL from `responses`; an Exception value is raised instead."""
    return _Probe(responses)


def _response(payload: object, status_code: int = 200) -> MagicMock:
    resp = MagicMock()
    resp.status_code = status_code
    resp.json.return_value = payload
    resp.text = str(payload)
    return resp


def _ctx(servers: dict[str, Any], http: _Probe | None) -> MagicMock:
    """A context with no LLM or embed endpoints, so only the MCP posture path runs."""
    ctx = MagicMock()
    ctx.cfg.mcp.mcp_servers = servers
    ctx.cfg.llm.llm_url = ""
    ctx.cfg.rag.embed_url = ""
    ctx.services_required.http = http
    return ctx


def _security_block(
    server_key: str = SERVER_KEY, **overrides: object
) -> dict[str, object]:
    """A `security` block exactly as a server publishes it, with every required check OK."""
    checks = [
        {"id": check_id, "status": "ok", "reason_code": "ok", "message": "check passed"}
        for check_id in REQUIRED_CHECK_IDS[server_key]
    ]
    data: dict[str, object] = {
        "contract_version": SECURITY_CONTRACT_VERSION,
        "server_key": server_key,
        "policy_version": "1",
        "validated": True,
        "ready": True,
        "fingerprint": FINGERPRINT,
        "checks": checks,
    }
    data.update(overrides)
    return data


def _body(
    posture: dict[str, object] | None = None, **extra: object
) -> dict[str, object]:
    body: dict[str, object] = {"service": "mdq-mcp", "ready": True, "dependencies": {}}
    if posture is not None:
        body["security"] = posture
    body.update(extra)
    return body


def _gate(**overrides: Any) -> PostureGate:
    """A fully green gate, overridden per case."""
    data: dict[str, Any] = {
        "server_key": SERVER_KEY,
        "required": True,
        "reachable": True,
        "posture_accepted": True,
        "ready": True,
        "validated": True,
        "reason_code": REASON_OK,
    }
    data.update(overrides)
    return PostureGate(**data)


class TestCollectServerPostures:
    """One probe per usable server, and every answer becomes a gate with a reason code."""

    async def test_conforming_posture_produces_a_green_gate(self) -> None:
        http = _http({HEALTH_URL: _response(_body(_security_block()))})
        gates = await collect_server_postures(_ctx({SERVER_KEY: _server()}, http))
        gate = gates[SERVER_KEY]
        assert gate.failure_class is None
        assert gate.reason_code == REASON_OK
        assert (gate.reachable, gate.posture_accepted, gate.ready, gate.validated) == (
            True,
            True,
            True,
            True,
        )

    async def test_each_server_is_probed_exactly_once(self) -> None:
        http = _http(
            {
                HEALTH_URL: _response(_body(_security_block())),
                "http://other:1/health": _response(_body(_security_block("file_read"))),
            }
        )
        ctx = _ctx(
            {
                SERVER_KEY: _server(),
                "file_read": _server("http://other:1"),
            },
            http,
        )
        gates = await collect_server_postures(ctx)
        assert len(gates) == 2
        assert len(http.calls) == 2

    async def test_auth_headers_are_sent_to_the_probe(self) -> None:
        http = _http({HEALTH_URL: _response(_body(_security_block()))})
        cfg = _server(auth_token="probe-token")
        await collect_server_postures(_ctx({SERVER_KEY: cfg}, http))
        assert http.calls[0][1]["headers"] == {"Authorization": "Bearer probe-token"}

    async def test_unreachable_server_is_an_availability_gate(self) -> None:
        http = _http({HEALTH_URL: httpx.ConnectError("connection refused")})
        gates = await collect_server_postures(_ctx({SERVER_KEY: _server()}, http))
        gate = gates[SERVER_KEY]
        assert gate.failure_class is ServerFailureClass.AVAILABILITY
        assert gate.reason_code == REASON_DEPENDENCY_UNREACHABLE
        assert gate.reachable is False

    async def test_unparsable_body_is_an_availability_gate(self) -> None:
        resp = _response(None)
        resp.json.side_effect = ValueError("not json")
        http = _http({HEALTH_URL: resp})
        gates = await collect_server_postures(_ctx({SERVER_KEY: _server()}, http))
        assert gates[SERVER_KEY].failure_class is ServerFailureClass.AVAILABILITY
        assert gates[SERVER_KEY].reason_code == REASON_CONFIG_INVALID

    async def test_missing_security_block_is_an_integrity_gate(self) -> None:
        http = _http({HEALTH_URL: _response(_body())})
        gates = await collect_server_postures(_ctx({SERVER_KEY: _server()}, http))
        assert gates[SERVER_KEY].failure_class is ServerFailureClass.INTEGRITY
        assert gates[SERVER_KEY].reason_code == REASON_POSTURE_MISSING

    async def test_contract_version_mismatch_is_an_integrity_gate(self) -> None:
        http = _http(
            {HEALTH_URL: _response(_body(_security_block(contract_version="99")))}
        )
        gates = await collect_server_postures(_ctx({SERVER_KEY: _server()}, http))
        assert gates[SERVER_KEY].failure_class is ServerFailureClass.INTEGRITY
        assert gates[SERVER_KEY].reason_code == REASON_CONTRACT_VERSION_MISMATCH

    async def test_missing_required_check_is_an_integrity_gate(self) -> None:
        checks = _security_block()["checks"]
        assert isinstance(checks, list)
        checks.pop(0)
        http = _http({HEALTH_URL: _response(_body(_security_block(checks=checks)))})
        gates = await collect_server_postures(_ctx({SERVER_KEY: _server()}, http))
        assert gates[SERVER_KEY].failure_class is ServerFailureClass.INTEGRITY
        assert gates[SERVER_KEY].reason_code == REASON_CHECK_SET_MISMATCH

    async def test_a_posture_for_another_server_key_is_an_integrity_gate(self) -> None:
        http = _http({HEALTH_URL: _response(_body(_security_block("file_read")))})
        gates = await collect_server_postures(_ctx({SERVER_KEY: _server()}, http))
        assert gates[SERVER_KEY].failure_class is ServerFailureClass.INTEGRITY
        assert gates[SERVER_KEY].reason_code == REASON_SERVER_KEY_MISMATCH

    async def test_an_unvalidated_posture_is_a_safety_gate(self) -> None:
        http = _http(
            {
                HEALTH_URL: _response(
                    _body(_security_block(validated=False, ready=False))
                )
            }
        )
        gates = await collect_server_postures(_ctx({SERVER_KEY: _server()}, http))
        assert gates[SERVER_KEY].failure_class is ServerFailureClass.SAFETY
        assert gates[SERVER_KEY].reason_code == REASON_OK
        assert gates[SERVER_KEY].validated is False

    async def test_a_validated_but_not_ready_posture_is_an_availability_gate(
        self,
    ) -> None:
        http = _http(
            {HEALTH_URL: _response(_body(_security_block(ready=False), ready=False))}
        )
        gates = await collect_server_postures(_ctx({SERVER_KEY: _server()}, http))
        assert gates[SERVER_KEY].failure_class is ServerFailureClass.AVAILABILITY
        assert gates[SERVER_KEY].ready is False

    async def test_a_disabled_server_is_not_probed_or_gated(self) -> None:
        http = _http({HEALTH_URL: _response(_body(_security_block()))})
        ctx = _ctx({SERVER_KEY: _server(startup_mode=StartupMode.NONE)}, http)
        gates = await collect_server_postures(ctx)
        assert gates == {}
        assert http.calls == []

    async def test_a_server_without_a_url_is_not_probed_or_gated(self) -> None:
        http = _http({HEALTH_URL: _response(_body(_security_block()))})
        gates = await collect_server_postures(
            _ctx({SERVER_KEY: _fake_cfg(url="")}, http)
        )
        assert gates == {}
        assert http.calls == []

    async def test_a_non_http_transport_is_not_probed_or_gated(self) -> None:
        http = _http({HEALTH_URL: _response(_body(_security_block()))})
        gates = await collect_server_postures(
            _ctx({"legacy": _fake_cfg(transport="stdio")}, http)
        )
        assert gates == {}
        assert http.calls == []


class TestClassifyServerFailure:
    """The fixed order, and an unclassified rejection is still a failure."""

    def test_green_gate_has_no_failure(self) -> None:
        assert classify_server_failure(_gate()) is None

    def test_unreachable_wins_over_everything_else(self) -> None:
        gate = _gate(
            reachable=False,
            posture_accepted=False,
            ready=False,
            validated=False,
            reason_code=REASON_POSTURE_MISSING,
        )
        assert classify_server_failure(gate) is ServerFailureClass.AVAILABILITY

    def test_rejected_contract_is_integrity(self) -> None:
        gate = _gate(
            posture_accepted=False,
            ready=False,
            validated=False,
            reason_code=REASON_CONTRACT_VERSION_MISMATCH,
        )
        assert classify_server_failure(gate) is ServerFailureClass.INTEGRITY

    def test_an_unreadable_body_is_availability_not_integrity(self) -> None:
        gate = _gate(
            posture_accepted=False,
            ready=False,
            validated=False,
            reason_code=REASON_CONFIG_INVALID,
            parse_failed=True,
        )
        assert classify_server_failure(gate) is ServerFailureClass.AVAILABILITY

    def test_an_unknown_rejection_reason_is_still_a_failure(self) -> None:
        gate = _gate(
            posture_accepted=False,
            ready=False,
            validated=False,
            reason_code=REASON_AUTH_TOKEN_MISSING,
        )
        assert classify_server_failure(gate) is ServerFailureClass.AVAILABILITY

    def test_unvalidated_accepted_posture_is_safety(self) -> None:
        gate = _gate(ready=False, validated=False)
        assert classify_server_failure(gate) is ServerFailureClass.SAFETY

    def test_validated_but_not_ready_is_availability(self) -> None:
        gate = _gate(ready=False)
        assert classify_server_failure(gate) is ServerFailureClass.AVAILABILITY


class TestAllowedServerKeys:
    """Only a fully green gate earns a place in the registry."""

    def test_green_gate_is_allowed(self) -> None:
        assert allowed_server_keys({SERVER_KEY: _gate()}) == {SERVER_KEY}

    @pytest.mark.parametrize(
        "overrides",
        [
            {"reachable": False},
            {"posture_accepted": False},
            {"ready": False},
            {"validated": False},
            {"reachable": False, "posture_accepted": False},
        ],
    )
    def test_any_non_green_field_excludes_the_server(
        self, overrides: dict[str, Any]
    ) -> None:
        assert allowed_server_keys({SERVER_KEY: _gate(**overrides)}) == set()

    def test_gates_are_not_a_second_probe(self) -> None:
        assert allowed_server_keys({}) == set()


class TestCheckServiceHealthPosture:
    """Posture entries reuse the required-versus-optional shape only for availability failures."""

    async def test_green_server_produces_no_issue(self) -> None:
        http = _http({HEALTH_URL: _response(_body(_security_block()))})
        result = await check_service_health(_ctx({SERVER_KEY: _server()}, http))
        assert not result.has_issues

    async def test_required_server_failure_is_an_error(self) -> None:
        http = _http({HEALTH_URL: _response(_body())})
        result = await check_service_health(_ctx({SERVER_KEY: _server()}, http))
        assert [w.label for w in result.errors] == [f"mcp:{SERVER_KEY}"]
        assert "integrity" in result.errors[0].message
        assert f"reason={REASON_POSTURE_MISSING}" in result.errors[0].message
        assert result.warnings == []

    async def test_optional_server_integrity_failure_is_an_error(self) -> None:
        """ADR-004 INV-09/INV-10: `required = false` does not soften an Integrity failure."""
        http = _http({HEALTH_URL: _response(_body())})
        ctx = _ctx({SERVER_KEY: _server(required=False)}, http)
        result = await check_service_health(ctx)
        assert [w.label for w in result.errors] == [f"mcp:{SERVER_KEY}"]
        assert "integrity" in result.errors[0].message
        assert result.warnings == []

    async def test_optional_server_safety_failure_is_an_error(self) -> None:
        """A published posture with `validated = false` is fatal even for an optional server."""
        http = _http(
            {
                HEALTH_URL: _response(
                    _body(_security_block(validated=False, ready=False))
                )
            }
        )
        ctx = _ctx({SERVER_KEY: _server(required=False)}, http)
        result = await check_service_health(ctx)
        assert [w.label for w in result.errors] == [f"mcp:{SERVER_KEY}"]
        assert "safety" in result.errors[0].message
        assert result.warnings == []

    async def test_optional_server_availability_failure_is_a_warning(self) -> None:
        http = _http({HEALTH_URL: httpx.ConnectError("connection refused")})
        ctx = _ctx({SERVER_KEY: _server(required=False)}, http)
        result = await check_service_health(ctx)
        assert result.errors == []
        assert result.warnings[0].label == f"mcp:{SERVER_KEY}"
        assert "availability" in result.warnings[0].message
        assert result.warnings[0].message.startswith(OutputTag.NON_FATAL)

    async def test_llm_and_posture_failures_coexist(self) -> None:
        http = _http(
            {
                HEALTH_URL: _response(_body()),
                "http://llm:8000/health": httpx.ConnectError("llm down"),
            }
        )
        ctx = _ctx({SERVER_KEY: _server()}, http)
        ctx.cfg.llm.llm_url = "http://llm:8000/v1/chat/completions"
        result = await check_service_health(ctx)
        labels = [w.label for w in result.errors]
        assert labels == ["llm", f"mcp:{SERVER_KEY}"]

    async def test_missing_http_client_raises_before_any_probe(self) -> None:
        with pytest.raises(RuntimeError, match="http service not initialized"):
            await check_service_health(_ctx({SERVER_KEY: _server()}, None))

    async def test_warning_carries_the_configured_url(self) -> None:
        http = _http({HEALTH_URL: httpx.ConnectError("connection refused")})
        ctx = _ctx({SERVER_KEY: _server(required=False)}, http)
        result = await check_service_health(ctx)
        assert result.warnings[0].url == BASE_URL


class TestCheckReadinessPosture:
    """A Safety or Integrity failure aborts startup whatever `required` says."""

    async def test_integrity_failure_raises_with_remediation(self) -> None:
        http = _http({HEALTH_URL: _response(_body())})
        with pytest.raises(RuntimeError) as excinfo:
            await check_readiness(_ctx({SERVER_KEY: _server()}, http))
        message = str(excinfo.value)
        assert message.startswith(
            "Startup readiness check failed (required services unavailable)"
        )
        assert "integrity" in message
        assert "remediation" in message

    async def test_safety_failure_raises(self) -> None:
        http = _http(
            {
                HEALTH_URL: _response(
                    _body(_security_block(validated=False, ready=False))
                )
            }
        )
        with pytest.raises(RuntimeError) as excinfo:
            await check_readiness(_ctx({SERVER_KEY: _server()}, http))
        assert "safety" in str(excinfo.value)

    async def test_safety_failure_raises_for_an_optional_server(self) -> None:
        """ADR-004 INV-09/INV-10: `required = false` never turns a Safety failure into degraded mode."""
        http = _http(
            {
                HEALTH_URL: _response(
                    _body(_security_block(validated=False, ready=False))
                )
            }
        )
        ctx = _ctx({SERVER_KEY: _server(required=False)}, http)
        with pytest.raises(RuntimeError) as excinfo:
            await check_readiness(ctx)
        assert "safety" in str(excinfo.value)
        assert "remediation" in str(excinfo.value)

    async def test_availability_failure_for_an_optional_server_does_not_raise(
        self,
    ) -> None:
        http = _http({HEALTH_URL: httpx.ConnectError("connection refused")})
        ctx = _ctx({SERVER_KEY: _server(required=False)}, http)
        result = await check_readiness(ctx)
        assert len(result.warnings) == 1
        assert "availability" in result.warnings[0].message

    async def test_readiness_message_carries_no_fingerprint_or_server_text(
        self,
    ) -> None:
        checks = _security_block()["checks"]
        assert isinstance(checks, list)
        for entry in checks:
            entry["message"] = f"read {SECRET_TEXT} with {SECRET_TEXT}"
        posture = _security_block(validated=False, ready=False, checks=checks)
        http = _http({HEALTH_URL: _response(_body(posture, note=SECRET_TEXT))})
        with pytest.raises(RuntimeError) as excinfo:
            await check_readiness(_ctx({SERVER_KEY: _server()}, http))
        message = str(excinfo.value)
        assert SECRET_TEXT not in message
        assert FINGERPRINT not in message

    async def test_green_server_does_not_raise(self) -> None:
        http = _http({HEALTH_URL: _response(_body(_security_block()))})
        result = await check_readiness(_ctx({SERVER_KEY: _server()}, http))
        assert not result.has_issues


class TestStaticVsDynamicDisplay:
    """Static visibility and dynamic health render as two labeled values.

    Display composition contract for the /mcp status output (plan AC-4):
    static visibility is config-derived, dynamic health is the registry
    circuit state with a closed reason code and retry timing only for
    UNAVAILABLE/HALF_OPEN rows, and the display path performs no state
    transition.
    """

    @staticmethod
    def _probe(health: str, *, static_visibility: bool = True) -> McpProbeResult:
        return McpProbeResult(
            key=SERVER_KEY,
            transport="http",
            startup_mode="persistent",
            auth=False,
            tier=McpTier.READ_ONLY,
            role="",
            availability=McpAvailability.OK,
            health=health,
            endpoint=BASE_URL,
            static_visibility=static_visibility,
        )

    @staticmethod
    def _unavailable_registry() -> McpServerHealthRegistry:
        registry = McpServerHealthRegistry(
            failure_threshold=3, half_open_cooldown_sec=30.0
        )
        for _ in range(3):
            registry.record_failure(SERVER_KEY)
        return registry

    def test_disabled_server_shows_excluded_and_still_renders_dynamic_state(
        self,
    ) -> None:
        registry = McpServerHealthRegistry()
        registry.record_success(SERVER_KEY)
        static_line, dynamic_line = _format_availability_display(
            self._probe("HEALTHY", static_visibility=False), registry
        )
        assert static_line == "Static visibility: excluded"
        assert dynamic_line == "Dynamic health: HEALTHY"

    def test_enabled_server_shows_visible(self) -> None:
        static_line, _ = _format_availability_display(
            self._probe("HEALTHY", static_visibility=True), McpServerHealthRegistry()
        )
        assert static_line == "Static visibility: visible"

    def test_unavailable_row_carries_reason_and_retry_after(self) -> None:
        registry = self._unavailable_registry()
        _, dynamic_line = _format_availability_display(
            self._probe("UNAVAILABLE"), registry
        )
        retry_text = dynamic_line.split("retry_after=", 1)[1]
        retry_after = int(retry_text)
        assert dynamic_line.startswith(
            "Dynamic health: UNAVAILABLE reason=server_unavailable retry_after="
        )
        assert 0 <= retry_after <= 30

    def test_half_open_row_carries_reason_without_retry_after(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        registry = self._unavailable_registry()
        # Cooldown elapsed: is_unavailable() performs UNAVAILABLE → HALF_OPEN.
        elapsed = time.monotonic() + 31.0
        monkeypatch.setattr(time, "monotonic", lambda: elapsed)
        assert registry.is_unavailable(SERVER_KEY) is False
        assert registry.get_state(SERVER_KEY) == McpServerHealthState.HALF_OPEN
        _, dynamic_line = _format_availability_display(
            self._probe("HALF_OPEN"), registry
        )
        assert dynamic_line == (
            "Dynamic health: HALF_OPEN reason=half_open_trial_in_progress"
        )

    def test_healthy_row_carries_neither_reason_nor_retry_after(self) -> None:
        _, dynamic_line = _format_availability_display(
            self._probe("HEALTHY"), McpServerHealthRegistry()
        )
        assert dynamic_line == "Dynamic health: HEALTHY"

    def test_missing_registry_falls_back_to_reason_without_retry_after(self) -> None:
        _, dynamic_line = _format_availability_display(self._probe("UNAVAILABLE"), None)
        assert dynamic_line == "Dynamic health: UNAVAILABLE reason=server_unavailable"

    def test_display_path_performs_no_state_transition(self) -> None:
        registry = self._unavailable_registry()
        before = registry.get_state(SERVER_KEY)
        _format_availability_display(self._probe("UNAVAILABLE"), registry)
        _format_availability_display(self._probe("UNAVAILABLE"), registry)
        assert registry.get_state(SERVER_KEY) == before
