# Implementation: tests/test_mcp_health_degraded.py — Degraded MCP health tests

## Goal

Verify `record_degraded()`, watchdog integration, `/mcp status` display, and that degraded state does not block dispatch.

## Scope

**In**: Unit tests for `McpServerHealthRegistry`, watchdog integration tests, `/mcp status` display tests.

**Out**: Transport or dispatch behavior tests.

## Assumptions

1. `McpServerHealthRegistry` importable from `shared.mcp_health`.
2. `record_degraded()`, `get_degraded_reason()` methods exist after Plan 14 Phase 1.
3. Watchdog tests use mocked `ctx` with `health_registry`.
4. `is_unavailable()` must return `False` for DEGRADED.

## Implementation

### Target file
`tests/test_mcp_health_degraded.py`

### Procedure
Write unit tests for each acceptance criterion from the plan.

### Method

```python
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
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


# --- Watchdog integration tests ---

def _make_watchdog_ctx(with_registry=True):
    ctx = MagicMock()
    if with_registry:
        ctx.services_required.health_registry = McpServerHealthRegistry()
    else:
        ctx.services_required.health_registry = None
    return ctx


def _make_probe(reachable, restart_recommended, operator_action_required=False, body=None):
    probe = MagicMock()
    probe.reachable = reachable
    probe.restart_recommended = restart_recommended
    probe.operator_action_required = operator_action_required
    probe.body = body or {}
    return probe


@pytest.mark.asyncio
async def test_watchdog_reachable_not_restart_calls_record_degraded():
    from agent.repl_health import _watchdog_check_http
    ctx = _make_watchdog_ctx()
    probe = _make_probe(reachable=True, restart_recommended=False, body={"reason": "queue full"})
    restart_counts = {"srv1": 0}

    with patch("agent.repl_health._watchdog_probe_http", return_value=probe):
        await _watchdog_check_http(ctx, "srv1", restart_counts)

    assert ctx.services_required.health_registry.get_state("srv1") == McpServerHealthState.DEGRADED
    assert ctx.services_required.health_registry.get_degraded_reason("srv1") == "queue full"


@pytest.mark.asyncio
async def test_watchdog_reachable_restart_does_not_call_record_degraded():
    from agent.repl_health import _watchdog_check_http
    ctx = _make_watchdog_ctx()
    probe = _make_probe(reachable=True, restart_recommended=True)
    restart_counts = {"srv1": 0}

    with patch("agent.repl_health._watchdog_probe_http", return_value=probe):
        with patch("agent.repl_health._restart_mcp_server", return_value=None):
            await _watchdog_check_http(ctx, "srv1", restart_counts)

    assert ctx.services_required.health_registry.get_state("srv1") != McpServerHealthState.DEGRADED


@pytest.mark.asyncio
async def test_watchdog_unreachable_calls_record_failure():
    from agent.repl_health import _watchdog_check_http
    ctx = _make_watchdog_ctx()
    probe = _make_probe(reachable=False, restart_recommended=True)
    restart_counts = {"srv1": 0}

    with patch("agent.repl_health._watchdog_probe_http", return_value=probe):
        with patch("agent.repl_health._restart_mcp_server", return_value=None):
            await _watchdog_check_http(ctx, "srv1", restart_counts)

    state = ctx.services_required.health_registry.get_state("srv1")
    assert state != McpServerHealthState.HEALTHY


@pytest.mark.asyncio
async def test_watchdog_no_registry_no_error():
    from agent.repl_health import _watchdog_check_http
    ctx = _make_watchdog_ctx(with_registry=False)
    probe = _make_probe(reachable=True, restart_recommended=False)
    restart_counts = {"srv1": 0}

    with patch("agent.repl_health._watchdog_probe_http", return_value=probe):
        # Should not raise even with no registry
        await _watchdog_check_http(ctx, "srv1", restart_counts)
```

## Validation plan

- `uv run pytest tests/test_mcp_health_degraded.py -v` — all pass.
- Verify: `record_degraded()` sets DEGRADED and stores reason.
- Verify: `record_success()` clears DEGRADED and reason.
- Verify: `is_unavailable()` returns `False` for DEGRADED.
- Verify: watchdog calls `record_degraded()` for reachable+non-restart case.
- `ruff check tests/test_mcp_health_degraded.py` — 0 errors.
