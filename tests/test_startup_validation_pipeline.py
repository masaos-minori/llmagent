"""tests/test_startup_validation_pipeline.py
Tests for startup validation pipeline aggregation behaviour.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.shared.health_models import (
    HealthCheckResult,
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
    instance._check_embedding_dimensions = MagicMock()
    return instance


@pytest.mark.asyncio
async def test_all_checks_pass_no_raise(startup_instance) -> None:
    with (
        patch(f"{MODULE}.audit_security_defaults", return_value=[]),
        patch(
            f"{MODULE}.check_readiness",
            new_callable=AsyncMock,
            return_value=HealthCheckResult(),
        ),
        patch(
            f"{MODULE}.McpToolDiscoveryService",
            new_callable=MagicMock,
            return_value=MagicMock(
                discover_all=AsyncMock(
                    return_value=MagicMock(registry=None, findings=[], unreachable=[])
                )
            ),
        ),
        patch(f"{MODULE}.check_routing_drift", return_value=[]),
        patch(f"{MODULE}.check_routing_safety_tiers", return_value=[]),
        patch(f"{MODULE}.RagMaintenanceService") as mock_rag,
    ):
        mock_rag.return_value.consistency.return_value.is_consistent = True
        await startup_instance._check_services()


@pytest.mark.asyncio
async def test_single_fatal_readiness_raises(startup_instance) -> None:
    from agent.shared.health_models import ServiceWarning

    with (
        patch(f"{MODULE}.audit_security_defaults", return_value=[]),
        patch(
            f"{MODULE}.check_readiness",
            new_callable=AsyncMock,
            return_value=HealthCheckResult(
                errors=[ServiceWarning("llm", "http://llm", "LLM unreachable")]
            ),
        ),
        patch(
            f"{MODULE}.McpToolDiscoveryService",
            new_callable=MagicMock,
            return_value=MagicMock(
                discover_all=AsyncMock(
                    return_value=MagicMock(registry=None, findings=[], unreachable=[])
                )
            ),
        ),
        patch(f"{MODULE}.check_routing_drift", return_value=[]),
        patch(f"{MODULE}.check_routing_safety_tiers", return_value=[]),
        patch(f"{MODULE}.RagMaintenanceService") as mock_rag,
    ):
        mock_rag.return_value.consistency.return_value.is_consistent = True
        with pytest.raises(RuntimeError, match="Startup validation failed"):
            await startup_instance._check_services()


@pytest.mark.asyncio
async def test_security_audit_fatal_remaining_checks_still_run(
    startup_instance,
) -> None:
    readiness_mock = AsyncMock(return_value=HealthCheckResult())
    with (
        patch(
            f"{MODULE}.audit_security_defaults",
            side_effect=RuntimeError("auth_token missing"),
        ),
        patch(f"{MODULE}.check_readiness", readiness_mock),
        patch(
            f"{MODULE}.McpToolDiscoveryService",
            new_callable=MagicMock,
            return_value=MagicMock(
                discover_all=AsyncMock(
                    return_value=MagicMock(registry=None, findings=[], unreachable=[])
                )
            ),
        ),
        patch(f"{MODULE}.check_routing_drift", return_value=[]),
        patch(f"{MODULE}.check_routing_safety_tiers", return_value=[]),
        patch(f"{MODULE}.RagMaintenanceService") as mock_rag,
    ):
        mock_rag.return_value.consistency.return_value.is_consistent = True
        with pytest.raises(RuntimeError, match="Startup validation failed"):
            await startup_instance._check_services()
        readiness_mock.assert_called_once()


@pytest.mark.asyncio
async def test_multiple_fatals_all_in_error_message(startup_instance) -> None:
    from agent.shared.health_models import ServiceWarning

    with (
        patch(
            f"{MODULE}.audit_security_defaults",
            side_effect=RuntimeError("audit_error"),
        ),
        patch(
            f"{MODULE}.check_readiness",
            new_callable=AsyncMock,
            return_value=HealthCheckResult(
                errors=[ServiceWarning("llm", "http://llm", "readiness_error")]
            ),
        ),
        patch(
            f"{MODULE}.McpToolDiscoveryService",
            new_callable=MagicMock,
            return_value=MagicMock(
                discover_all=AsyncMock(
                    return_value=MagicMock(registry=None, findings=[], unreachable=[])
                )
            ),
        ),
        patch(f"{MODULE}.check_routing_drift", return_value=[]),
        patch(f"{MODULE}.check_routing_safety_tiers", return_value=[]),
        patch(f"{MODULE}.RagMaintenanceService") as mock_rag,
    ):
        mock_rag.return_value.consistency.return_value.is_consistent = True
        with pytest.raises(RuntimeError) as exc_info:
            await startup_instance._check_services()
        msg = str(exc_info.value)
        assert "audit_error" in msg
        assert "readiness_error" in msg


@pytest.mark.asyncio
async def test_warnings_only_no_raise(startup_instance) -> None:
    with (
        patch(f"{MODULE}.audit_security_defaults", return_value=["sandbox=none"]),
        patch(
            f"{MODULE}.check_readiness",
            new_callable=AsyncMock,
            return_value=HealthCheckResult(),
        ),
        patch(
            f"{MODULE}.McpToolDiscoveryService",
            new_callable=MagicMock,
            return_value=MagicMock(
                discover_all=AsyncMock(
                    return_value=MagicMock(registry=None, findings=[], unreachable=[])
                )
            ),
        ),
        patch(f"{MODULE}.check_routing_drift", return_value=[]),
        patch(f"{MODULE}.check_routing_safety_tiers", return_value=[]),
        patch(f"{MODULE}.RagMaintenanceService") as mock_rag,
    ):
        mock_rag.return_value.consistency.return_value.is_consistent = True
        await startup_instance._check_services()


@pytest.mark.asyncio
async def test_routing_drift_strict_true_raises_fatal(startup_instance) -> None:
    startup_instance._ctx.cfg.tool.routing_drift_strict = True
    with (
        patch(f"{MODULE}.audit_security_defaults", return_value=[]),
        patch(
            f"{MODULE}.check_readiness",
            new_callable=AsyncMock,
            return_value=HealthCheckResult(),
        ),
        patch(
            f"{MODULE}.McpToolDiscoveryService",
            new_callable=MagicMock,
            return_value=MagicMock(
                discover_all=AsyncMock(
                    return_value=MagicMock(registry=None, findings=[], unreachable=[])
                )
            ),
        ),
        patch(
            f"{MODULE}.check_routing_drift",
            side_effect=RuntimeError("routing drift detected: tool_names mismatch"),
        ),
        patch(f"{MODULE}.check_routing_safety_tiers", return_value=[]),
        patch(f"{MODULE}.RagMaintenanceService") as mock_rag,
    ):
        mock_rag.return_value.consistency.return_value.is_consistent = True
        with pytest.raises(RuntimeError, match="Startup validation failed"):
            await startup_instance._check_services()


@pytest.mark.asyncio
async def test_routing_drift_strict_false_warns_only(startup_instance) -> None:
    startup_instance._ctx.cfg.tool.routing_drift_strict = False
    with (
        patch(f"{MODULE}.audit_security_defaults", return_value=[]),
        patch(
            f"{MODULE}.check_readiness",
            new_callable=AsyncMock,
            return_value=HealthCheckResult(),
        ),
        patch(
            f"{MODULE}.McpToolDiscoveryService",
            new_callable=MagicMock,
            return_value=MagicMock(
                discover_all=AsyncMock(
                    return_value=MagicMock(registry=None, findings=[], unreachable=[])
                )
            ),
        ),
        patch(
            f"{MODULE}.check_routing_drift",
            return_value=["drift: tool foo missing from tool_definitions"],
        ),
        patch(f"{MODULE}.check_routing_safety_tiers", return_value=[]),
        patch(f"{MODULE}.RagMaintenanceService") as mock_rag,
    ):
        mock_rag.return_value.consistency.return_value.is_consistent = True
        await startup_instance._check_services()  # must not raise


@pytest.mark.asyncio
async def test_skipped_live_routing_no_raise(startup_instance) -> None:
    with (
        patch(f"{MODULE}.audit_security_defaults", return_value=[]),
        patch(
            f"{MODULE}.check_readiness",
            new_callable=AsyncMock,
            return_value=HealthCheckResult(),
        ),
        patch(
            f"{MODULE}.McpToolDiscoveryService",
            new_callable=MagicMock,
            return_value=MagicMock(
                discover_all=AsyncMock(side_effect=Exception("all servers unreachable"))
            ),
        ),
        patch(f"{MODULE}.check_routing_drift", return_value=[]),
        patch(f"{MODULE}.check_routing_safety_tiers", return_value=[]),
        patch(f"{MODULE}.RagMaintenanceService") as mock_rag,
    ):
        mock_rag.return_value.consistency.return_value.is_consistent = True
        await startup_instance._check_services()
