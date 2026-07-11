"""Tests for McpServerHealthRegistry degraded state tracking and watchdog integration."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from shared.mcp_health import McpServerHealthRegistry, McpServerHealthState

# --- McpServerHealthRegistry unit tests ---


def test_record_degraded_sets_degraded_state():
    registry = McpServerHealthRegistry()
    registry.record_degraded("srv1", reason="unhealthy")
    assert registry.get_state("srv1") == McpServerHealthState.DEGRADED


def test_record_degraded_stores_reason():
    registry = McpServerHealthRegistry()
    registry.record_degraded("srv1", reason="queue full")
    assert registry.get_degraded_reason("srv1") == "queue full"


def test_record_degraded_no_reason():
    registry = McpServerHealthRegistry()
    registry.record_degraded("srv1")
    assert registry.get_degraded_reason("srv1") is None


def test_degraded_does_not_make_unavailable():
    registry = McpServerHealthRegistry()
    registry.record_degraded("srv1", reason="slow")
    assert not registry.is_unavailable("srv1")


def test_record_success_clears_degraded():
    registry = McpServerHealthRegistry()
    registry.record_degraded("srv1", reason="bad")
    registry.record_success("srv1")
    assert registry.get_state("srv1") == McpServerHealthState.HEALTHY
    assert registry.get_degraded_reason("srv1") is None


def test_record_degraded_idempotent():
    registry = McpServerHealthRegistry()
    registry.record_degraded("srv1", reason="reason1")
    registry.record_degraded("srv1", reason="reason2")
    assert registry.get_degraded_reason("srv1") == "reason2"


def test_get_degraded_reason_unknown_server():
    registry = McpServerHealthRegistry()
    assert registry.get_degraded_reason("unknown") is None


def test_record_restart_exhausted_sets_reason():
    registry = McpServerHealthRegistry()
    registry.record_restart_exhausted("srv1")
    assert registry.get_degraded_reason("srv1") == "restart_limit_reached"


def test_record_restart_exhausted_does_not_change_state():
    registry = McpServerHealthRegistry(failure_threshold=1)
    registry.record_failure("srv1")
    assert registry.get_state("srv1") == McpServerHealthState.UNAVAILABLE

    registry.record_restart_exhausted("srv1")

    assert registry.get_state("srv1") == McpServerHealthState.UNAVAILABLE
    assert registry.get_degraded_reason("srv1") == "restart_limit_reached"


def test_record_restart_exhausted_overwrites_prior_reason():
    registry = McpServerHealthRegistry()
    registry.record_degraded("srv1", reason="queue full")

    registry.record_restart_exhausted("srv1")

    assert registry.get_degraded_reason("srv1") == "restart_limit_reached"


def test_record_degraded_does_not_downgrade_unavailable():
    registry = McpServerHealthRegistry(failure_threshold=1)
    registry.record_failure("srv1")
    assert registry.get_state("srv1") == McpServerHealthState.UNAVAILABLE

    registry.record_degraded("srv1", reason="reachable but slow")

    assert registry.get_state("srv1") == McpServerHealthState.UNAVAILABLE
    assert registry.get_degraded_reason("srv1") is None


def test_record_degraded_does_not_downgrade_half_open():
    registry = McpServerHealthRegistry(failure_threshold=1, half_open_cooldown_sec=0.0)
    registry.record_failure("srv1")
    # Cooldown elapsed immediately (0.0s); is_unavailable() transitions to HALF_OPEN.
    assert registry.is_unavailable("srv1") is False
    assert registry.get_state("srv1") == McpServerHealthState.HALF_OPEN

    registry.record_degraded("srv1", reason="reachable but slow")

    assert registry.get_state("srv1") == McpServerHealthState.HALF_OPEN
    assert registry.get_degraded_reason("srv1") is None


def test_record_failure_below_threshold_sets_degraded():
    registry = McpServerHealthRegistry(failure_threshold=3)
    registry.record_failure("srv1")
    assert registry.get_state("srv1") == McpServerHealthState.DEGRADED


def test_record_failure_reaches_threshold_sets_unavailable():
    registry = McpServerHealthRegistry(failure_threshold=3)
    registry.record_failure("srv1")
    registry.record_failure("srv1")
    registry.record_failure("srv1")
    assert registry.get_state("srv1") == McpServerHealthState.UNAVAILABLE


def test_is_unavailable_transitions_to_half_open_after_cooldown():
    registry = McpServerHealthRegistry(failure_threshold=1, half_open_cooldown_sec=0.0)
    registry.record_failure("srv1")
    assert registry.get_state("srv1") == McpServerHealthState.UNAVAILABLE
    assert registry.is_unavailable("srv1") is False
    assert registry.get_state("srv1") == McpServerHealthState.HALF_OPEN


def test_record_success_from_half_open_sets_healthy():
    registry = McpServerHealthRegistry(failure_threshold=1, half_open_cooldown_sec=0.0)
    registry.record_failure("srv1")
    assert registry.is_unavailable("srv1") is False
    assert registry.get_state("srv1") == McpServerHealthState.HALF_OPEN
    registry.record_success("srv1")
    assert registry.get_state("srv1") == McpServerHealthState.HEALTHY


def test_record_failure_from_half_open_sets_unavailable_and_resets_cooldown():
    registry = McpServerHealthRegistry(failure_threshold=1, half_open_cooldown_sec=30.0)
    with patch("time.monotonic", return_value=100.0):
        registry.record_failure("srv1")
        assert registry.get_state("srv1") == McpServerHealthState.UNAVAILABLE
        assert registry.is_unavailable("srv1") is True

        # Simulate cooldown elapsing — transition to HALF_OPEN
        with patch("time.monotonic", return_value=131.0):
            assert registry.is_unavailable("srv1") is False
            assert registry.get_state("srv1") == McpServerHealthState.HALF_OPEN

            # Another failure while HALF_OPEN — back to UNAVAILABLE, cooldown reset
            with patch("time.monotonic", return_value=132.0):
                registry.record_failure("srv1")
                assert registry.get_state("srv1") == McpServerHealthState.UNAVAILABLE
                assert registry.is_unavailable("srv1") is True


def test_record_success_resets_failure_count_and_unavailable_timestamp():
    registry = McpServerHealthRegistry(failure_threshold=3)
    registry.record_failure("srv1")
    registry.record_failure("srv1")
    assert registry.get_state("srv1") == McpServerHealthState.DEGRADED
    registry.record_success("srv1")
    assert registry.get_state("srv1") == McpServerHealthState.HEALTHY
    registry.record_failure("srv1")
    assert registry.get_state("srv1") == McpServerHealthState.DEGRADED


# --- Watchdog integration tests ---


def _make_watchdog_ctx(with_registry=True):
    ctx = MagicMock()
    ctx.services_required.http = AsyncMock()
    ctx.services_required.lifecycle = None
    if with_registry:
        ctx.services_required.health_registry = McpServerHealthRegistry()
    else:
        ctx.services_required.health_registry = None
    return ctx


def _srv_cfg(url="http://srv1.test"):
    srv = MagicMock()
    srv.url = url
    srv.startup_mode = "persistent"
    return srv


def _make_probe(
    reachable,
    restart_recommended,
    operator_action_required=False,
    body=None,
    parse_failed=False,
):
    probe = MagicMock()
    probe.reachable = reachable
    probe.status_code = 503  # != HTTPStatus.OK; prevents entering the healthy branch
    probe.restart_recommended = restart_recommended
    probe.operator_action_required = operator_action_required
    probe.parse_failed = parse_failed
    probe.body = body if body is not None else {}
    return probe


@pytest.mark.asyncio
async def test_watchdog_reachable_not_restart_calls_record_degraded():
    from agent.repl_health import _watchdog_check_http

    ctx = _make_watchdog_ctx()
    probe = _make_probe(
        reachable=True, restart_recommended=False, body={"reason": "queue full"}
    )

    with patch(
        "agent.repl_health._probe_mcp_health_detail", new=AsyncMock(return_value=probe)
    ):
        await _watchdog_check_http(ctx, "srv1", _srv_cfg(), {"srv1": 0}, max_restarts=3)

    assert (
        ctx.services_required.health_registry.get_state("srv1")
        == McpServerHealthState.DEGRADED
    )
    assert (
        ctx.services_required.health_registry.get_degraded_reason("srv1")
        == "queue full"
    )


@pytest.mark.asyncio
async def test_watchdog_reachable_restart_does_not_call_record_degraded():
    from agent.repl_health import _watchdog_check_http

    ctx = _make_watchdog_ctx()
    probe = _make_probe(reachable=True, restart_recommended=True)

    with patch(
        "agent.repl_health._probe_mcp_health_detail", new=AsyncMock(return_value=probe)
    ):
        await _watchdog_check_http(ctx, "srv1", _srv_cfg(), {"srv1": 0}, max_restarts=3)

    # record_degraded was not called; no stored reason
    assert ctx.services_required.health_registry.get_degraded_reason("srv1") is None


@pytest.mark.asyncio
async def test_watchdog_unreachable_calls_record_failure():
    from agent.repl_health import _watchdog_check_http

    ctx = _make_watchdog_ctx()
    probe = _make_probe(reachable=False, restart_recommended=True)

    with patch(
        "agent.repl_health._probe_mcp_health_detail", new=AsyncMock(return_value=probe)
    ):
        await _watchdog_check_http(ctx, "srv1", _srv_cfg(), {"srv1": 0}, max_restarts=3)

    state = ctx.services_required.health_registry.get_state("srv1")
    assert state != McpServerHealthState.HEALTHY


@pytest.mark.asyncio
async def test_watchdog_no_registry_no_error():
    from agent.repl_health import _watchdog_check_http

    ctx = _make_watchdog_ctx(with_registry=False)
    probe = _make_probe(reachable=True, restart_recommended=False)

    with patch(
        "agent.repl_health._probe_mcp_health_detail", new=AsyncMock(return_value=probe)
    ):
        # Should not raise even with no registry
        await _watchdog_check_http(ctx, "srv1", _srv_cfg(), {"srv1": 0}, max_restarts=3)


def _make_probe_full(
    reachable=True,
    status_code=None,
    restart_recommended=False,
    operator_action_required=False,
    body=None,
    parse_failed=False,
    parse_error=None,
):
    """Construct a full McpHealthProbeResult without mocking."""
    from agent.shared.health_models import McpHealthProbeResult

    return McpHealthProbeResult(
        reachable=reachable,
        status_code=status_code,
        restart_recommended=restart_recommended,
        operator_action_required=operator_action_required,
        body=body if body is not None else {},
        parse_failed=parse_failed,
        parse_error=parse_error,
    )


@pytest.mark.asyncio
async def test_watchdog_malformed_json_calls_record_degraded_with_reason():
    from agent.repl_health import _watchdog_check_http

    ctx = _make_watchdog_ctx()
    probe = _make_probe_full(
        reachable=True,
        status_code=200,
        restart_recommended=False,
        operator_action_required=False,
        body={},
        parse_failed=True,
        parse_error="unexpected token",
    )

    with patch(
        "agent.repl_health._probe_mcp_health_detail", new=AsyncMock(return_value=probe)
    ):
        await _watchdog_check_http(ctx, "srv1", _srv_cfg(), {"srv1": 0}, max_restarts=3)

    assert (
        ctx.services_required.health_registry.get_state("srv1")
        == McpServerHealthState.DEGRADED
    )
    assert (
        ctx.services_required.health_registry.get_degraded_reason("srv1")
        == "malformed_health_response"
    )


@pytest.mark.asyncio
async def test_watchdog_degraded_with_restart_recommended_true_no_record_degraded():
    from agent.repl_health import _watchdog_check_http

    ctx = _make_watchdog_ctx()
    probe = _make_probe_full(reachable=True, status_code=200, restart_recommended=True)

    with patch(
        "agent.repl_health._probe_mcp_health_detail", new=AsyncMock(return_value=probe)
    ):
        await _watchdog_check_http(ctx, "srv1", _srv_cfg(), {"srv1": 0}, max_restarts=3)

    # Degraded + restart recommended goes through restart path, NOT record_degraded
    assert ctx.services_required.health_registry.get_degraded_reason("srv1") is None


def test_classify_health_failure_all_five_cases():
    from agent.repl_health import _classify_health_failure

    unreachable = _make_probe_full(reachable=False)
    assert _classify_health_failure(unreachable) == "unreachable"

    malformed = _make_probe_full(
        reachable=True, status_code=200, parse_failed=True, parse_error="bad json"
    )
    result = _classify_health_failure(malformed)
    assert "malformed JSON" in result
    assert "bad json" in result

    non_200 = _make_probe_full(reachable=True, status_code=503)
    result = _classify_health_failure(non_200)
    assert "non-200" in result
    assert "status=503" in result

    degraded_no_restart = _make_probe_full(
        reachable=True, status_code=200, restart_recommended=False
    )
    assert (
        _classify_health_failure(degraded_no_restart)
        == "degraded (restart_recommended=false)"
    )

    degraded_restart = _make_probe_full(
        reachable=True, status_code=200, restart_recommended=True
    )
    assert (
        _classify_health_failure(degraded_restart)
        == "degraded (restart_recommended=true)"
    )
