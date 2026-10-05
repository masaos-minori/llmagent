"""tests/agent/test_startup_validation.py

Regression tests for REQ-002, REQ-003: Verify the RAG consistency check inside
StartupValidationPipeline.check_services() enforces its timeout and reports a
normal pass, by driving the real check_services() body.
"""

from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.shared.health_models import (
    HealthCheckResult,
    StartupCheckStatus,
    StartupValidationResult,
)
from agent.startup_validation import StartupValidationPipeline
from shared.mcp_config import SecurityProfile


def _make_ctx() -> MagicMock:
    ctx = MagicMock()
    ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION
    ctx.cfg.memory.memory_embed_dim = 768
    ctx.cfg.tool.tool_definitions_strict = False
    return ctx


async def _run_check_services(
    rag_service: MagicMock,
    *,
    wait_for_side_effect: BaseException | None = None,
) -> StartupValidationResult:
    """Run the real check_services() with every other check mocked to a clean pass."""
    ctx = _make_ctx()
    discovery = MagicMock(
        return_value=MagicMock(
            discover_all=AsyncMock(
                return_value=MagicMock(registry=None, findings=[], unreachable=[])
            )
        )
    )
    mocks: dict[str, object] = {
        "audit_security_defaults": MagicMock(return_value=[]),
        "check_readiness": AsyncMock(return_value=HealthCheckResult()),
        "McpToolDiscoveryService": discovery,
        "check_routing_drift": MagicMock(return_value=[]),
        "check_routing_safety_tiers": MagicMock(return_value=[]),
        "RagMaintenanceService": MagicMock(return_value=rag_service),
    }
    with ExitStack() as stack:
        for name, mock_obj in mocks.items():
            stack.enter_context(patch(f"agent.startup_validation.{name}", mock_obj))
        stack.enter_context(
            patch(
                "db.config.build_db_config",
                return_value=MagicMock(embedding_dims=768),
            )
        )
        # check_services() builds its own Logger; keep it from touching log files.
        stack.enter_context(patch("shared.logger.Logger", MagicMock()))
        if wait_for_side_effect is not None:
            stack.enter_context(
                patch(
                    "agent.startup_validation.asyncio.wait_for",
                    side_effect=wait_for_side_effect,
                )
            )
        return await StartupValidationPipeline(ctx, MagicMock()).check_services()


def _rag_outcomes(result: StartupValidationResult) -> list[StartupCheckStatus]:
    return [o.status for o in result.outcomes if o.source == "rag_consistency"]


class TestRagConsistencyTimeout:
    """Tests for REQ-002, REQ-003: RAG check timeout enforcement."""

    @pytest.mark.asyncio
    async def test_rag_check_timeout_enforced(self) -> None:
        """REQ-002: a timed-out RAG consistency check is skipped, not fatal."""
        rag_service = MagicMock()
        result = await _run_check_services(
            rag_service,
            wait_for_side_effect=TimeoutError("timed out"),
        )

        assert _rag_outcomes(result) == [StartupCheckStatus.SKIPPED]
        skipped = [o for o in result.outcomes if o.source == "rag_consistency"]
        assert "timeout" in skipped[0].message
        assert not result.has_fatal

    @pytest.mark.asyncio
    async def test_rag_check_succeeds_within_timeout(self) -> None:
        """REQ-003: a normal RAG check reports OK."""
        rag_service = MagicMock()
        rag_service.consistency.return_value = MagicMock(is_consistent=True, issues=[])

        result = await _run_check_services(rag_service)

        assert _rag_outcomes(result) == [StartupCheckStatus.OK]
        rag_service.consistency.assert_called_once()
