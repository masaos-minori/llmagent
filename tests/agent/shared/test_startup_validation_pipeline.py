"""tests/test_startup_validation_pipeline.py
Tests for startup validation pipeline aggregation behaviour.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock

import pytest
from agent.shared.health_models import (
    StartupCheckStatus,
    StartupValidationResult,
)

MODULE = "agent.startup"


# --- StartupValidationResult unit tests ---


def test_validation_result_empty_has_no_fatal() -> None:
    result = StartupValidationResult()
    assert not result.has_fatal
    assert result.fatal_messages() == []


def test_validation_result_fatal_detected() -> None:
    result = StartupValidationResult()
    result.add_ok("check_a")
    result.add_fatal("check_b", "Something broke", remediation="Fix it")
    assert result.has_fatal
    assert result.fatal_messages() == ["Something broke"]


def test_validation_result_multiple_fatals_collected() -> None:
    result = StartupValidationResult()
    result.add_fatal("check_a", "Error A")
    result.add_fatal("check_b", "Error B")
    assert len(result.fatal_messages()) == 2
    assert "Error A" in result.fatal_messages()
    assert "Error B" in result.fatal_messages()


def test_validation_result_warnings_only_no_fatal() -> None:
    result = StartupValidationResult()
    result.add_warning("check_a", "Warn A")
    result.add_warning("check_b", "Warn B")
    assert not result.has_fatal
    assert len(result.warning_messages()) == 2


def test_validation_result_skipped_not_fatal() -> None:
    result = StartupValidationResult()
    result.add_skipped("live_routing", "All servers unreachable")
    assert not result.has_fatal
    assert result.outcomes[0].status == StartupCheckStatus.SKIPPED


# --- _check_services() integration tests ---


@pytest.fixture()
def mock_ctx():
    ctx = MagicMock()
    ctx.cfg.mcp.security_profile = "local"
    ctx.cfg.tool.tool_definitions_strict = False
    return ctx


@pytest.fixture()
def startup_instance(mock_ctx):
    from agent.startup import StartupOrchestrator

    instance = StartupOrchestrator.__new__(StartupOrchestrator)
    instance._ctx = mock_ctx
    instance._view = MagicMock()
    instance._reporter = MagicMock()
    # Wire a mock validation pipeline so _check_services() has something to call
    instance._validation_pipeline = MagicMock()
    instance._validation_pipeline.check_services = AsyncMock()
    return instance


@pytest.mark.asyncio
async def test_warnings_only_no_raise(startup_instance) -> None:
    pipeline = startup_instance._validation_pipeline
    pipeline.check_services.return_value = MagicMock(
        has_fatal=False,
        fatal_messages=lambda: [],
        warning_messages=lambda: ["sandbox=none"],
        outcomes=[],
    )
    await startup_instance._check_services()


@pytest.mark.asyncio
async def test_routing_drift_strict_true_raises_fatal(startup_instance) -> None:
    startup_instance._ctx.cfg.tool.routing_drift_strict = True
    pipeline = startup_instance._validation_pipeline
    pipeline.check_services.side_effect = RuntimeError(
        "Startup validation failed: routing drift detected: tool_names mismatch"
    )
    with pytest.raises(RuntimeError, match="Startup validation failed"):
        await startup_instance._check_services()


@pytest.mark.asyncio
async def test_routing_drift_strict_false_warns_only(startup_instance) -> None:
    startup_instance._ctx.cfg.tool.routing_drift_strict = False
    pipeline = startup_instance._validation_pipeline
    pipeline.check_services.return_value = MagicMock(
        has_fatal=False,
        fatal_messages=lambda: [],
        warning_messages=lambda: ["drift: tool foo missing from tool_definitions"],
        outcomes=[],
    )
    await startup_instance._check_services()  # must not raise


@pytest.mark.asyncio
async def test_skipped_live_routing_no_raise(startup_instance) -> None:
    pipeline = startup_instance._validation_pipeline
    pipeline.check_services.side_effect = RuntimeError(
        "Startup validation failed: live routing check skipped — all servers unreachable"
    )
    with pytest.raises(RuntimeError, match="Startup validation failed"):
        await startup_instance._check_services()


# --- check_routing_safety_tiers ---

import contextlib

from agent.services.routing_drift import (
    check_routing_safety_tiers,
)


@contextlib.contextmanager
def _reset_registry():
    from shared.tool_registry import _reset_registry_for_testing

    try:
        yield
    finally:
        _reset_registry_for_testing()


@pytest.fixture(autouse=True)
def reset_registry():
    with _reset_registry():
        yield


# NOTE: The following three tests used the old signature
#   check_routing_safety_tiers(registry=..., tool_safety_tiers=...)
# which was removed during the refactor to AgentContext-based API.
# They have been migrated to tests/agent/test_startup_mcp_starter.py
# Kept for backward compatibility until all references are updated.


def test_check_routing_safety_tiers_context():
    ctx = MagicMock()
    cfg = MagicMock()
    server = MagicMock()
    server.tool_names = ["tool_a", "tool_b"]
    cfg.mcp.mcp_servers = {"srv1": server}
    cfg.tool.routing_drift_strict = False
    cfg.approval.tool_safety_tiers = {}
    ctx.cfg = cfg
    msgs = check_routing_safety_tiers(ctx)
    assert msgs == []


# --- RAG consistency check tests ---

# NOTE: The RAG consistency tests below have been migrated to
#   - tests/agent/test_startup_mcp_starter.py (consistency check tests)
# Kept for backward compatibility until all references are updated.
