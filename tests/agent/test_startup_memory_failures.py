"""Behavior-lock tests proving each memory-failure path's documented severity is produced under its condition."""

from __future__ import annotations

from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.shared.health_models import (
    HealthCheckResult,
    ServiceWarning,
    StartupCheckOutcome,
    StartupCheckStatus,
    StartupValidationResult,
)
from agent.startup import StartupOrchestrator
from shared.mcp_config import SecurityProfile


def _make_startup_ctx(
    *,
    memory_embed_dim: int = 768,
    tool_definitions_strict: bool = False,
) -> MagicMock:
    """Return a ctx MagicMock configured for _check_services() tests."""
    ctx = MagicMock()
    ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION
    ctx.cfg.memory.memory_embed_dim = memory_embed_dim
    ctx.cfg.tool.tool_definitions_strict = tool_definitions_strict
    return ctx


async def _run_check_services(
    ctx: MagicMock,
    *,
    embedding_dims: int | None = None,
    **overrides: object,
) -> tuple[StartupValidationResult, Exception | None]:
    """Run StartupOrchestrator._check_services() with clean-pass mocks for all 8 checks,
    overridden per-test via kwargs (named after the agent.startup_validation import site), and return
    (captured pipeline outcomes, exception raised by _check_services() or None).
    """
    consistent_rag = MagicMock()
    consistent_rag.consistency.return_value = MagicMock(is_consistent=True, issues=[])
    mocks: dict[str, object] = {
        "audit_security_defaults": MagicMock(return_value=[]),
        "check_readiness": AsyncMock(return_value=HealthCheckResult()),
        "McpToolDiscoveryService": MagicMock(
            return_value=MagicMock(
                discover_all=AsyncMock(
                    return_value=MagicMock(registry=None, findings=[], unreachable=[])
                )
            )
        ),
        "check_routing_drift": MagicMock(return_value=[]),
        "check_routing_safety_tiers": MagicMock(return_value=[]),
        "RagMaintenanceService": MagicMock(return_value=consistent_rag),
    }
    mocks.update(overrides)

    if embedding_dims is None:
        embedding_dims = (
            ctx.cfg.memory.memory_embed_dim
        )  # clean pass: dims match by default

    captured: dict[str, StartupValidationResult] = {}

    def _new_pipeline() -> StartupValidationResult:
        pipeline = StartupValidationResult()
        captured["pipeline"] = pipeline
        return pipeline

    startup = StartupOrchestrator(ctx, MagicMock())
    from agent.startup_validation import StartupValidationPipeline

    startup._validation_pipeline = StartupValidationPipeline(ctx, startup._view)
    startup._reporter = MagicMock()

    exc: Exception | None = None
    with ExitStack() as stack:
        for name, mock_obj in mocks.items():
            stack.enter_context(patch(f"agent.startup_validation.{name}", mock_obj))
        stack.enter_context(
            patch(
                "agent.startup_validation.StartupValidationResult",
                side_effect=_new_pipeline,
            )
        )
        stack.enter_context(
            patch(
                "db.config.build_db_config",
                return_value=MagicMock(embedding_dims=embedding_dims),
            )
        )
        try:
            await startup._check_services()
        except Exception as e:  # noqa: BLE001 — intentionally capturing any exception to return it
            exc = e
    return captured["pipeline"], exc


class TestStartupMemoryFailures:
    """Regression tests proving each memory-failure path's documented severity is actually produced
    under its documented condition — see docs/05_agent_10_01_...startup-and-health.md's
    severity-mapping table for the full narrative this cross-references."""

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Feature not implemented: memory_embed_dim validation")
    async def test_embedding_dimensions_fatal_when_mismatch(self) -> None:
        """FATAL when memory_embed_dim doesn't match db config (e.g. migration needed)."""
        ctx = _make_startup_ctx(memory_embed_dim=768)
        pipeline, exc = await _run_check_services(
            ctx,
            embedding_dims=1536,
        )
        assert exc is not None
        outcomes = [o for o in pipeline.outcomes if o.source == "embedding_dimensions"]
        assert any(o.status == StartupCheckStatus.FATAL for o in outcomes)

    @pytest.mark.asyncio
    @pytest.mark.skip(reason="Feature not implemented: memory_embed_dim validation")
    async def test_embedding_dimensions_ok_when_match(self) -> None:
        """OK when memory_embed_dim matches db config (no migration needed)."""
        ctx = _make_startup_ctx(memory_embed_dim=768)
        pipeline, exc = await _run_check_services(
            ctx,
            embedding_dims=768,
        )
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "embedding_dimensions"]
        assert any(o.status == StartupCheckStatus.OK for o in outcomes)

    @pytest.mark.asyncio
    async def test_tool_definitions_strict_fatal_on_finding(self) -> None:
        """A strict-mode finding from discover_all() is surfaced as FATAL."""
        ctx = _make_startup_ctx(tool_definitions_strict=True)
        finding = StartupCheckOutcome(
            "drift_detected", StartupCheckStatus.FATAL, "drift in strict mode"
        )
        discovery_result = MagicMock(registry=None, findings=[finding], unreachable=[])
        pipeline, exc = await _run_check_services(
            ctx,
            McpToolDiscoveryService=MagicMock(
                return_value=MagicMock(
                    discover_all=AsyncMock(return_value=discovery_result)
                )
            ),
        )
        assert exc is not None
        assert isinstance(exc, RuntimeError)
        assert "drift in strict mode" in str(exc)
        outcomes = [o for o in pipeline.outcomes if o.source == "mcp_tool_discovery"]
        assert any(o.status == StartupCheckStatus.FATAL for o in outcomes)

    @pytest.mark.asyncio
    async def test_tool_definitions_warning_on_non_strict_finding(self) -> None:
        """Non-strict-mode finding from discover_all() is WARNING, not FATAL."""
        ctx = _make_startup_ctx(tool_definitions_strict=False)
        finding = StartupCheckOutcome(
            "drift_detected",
            StartupCheckStatus.WARNING,
            "non-strict drift",
        )
        discovery_result = MagicMock(registry=None, findings=[finding], unreachable=[])
        pipeline, exc = await _run_check_services(
            ctx,
            McpToolDiscoveryService=MagicMock(
                return_value=MagicMock(
                    discover_all=AsyncMock(return_value=discovery_result)
                )
            ),
        )
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "mcp_tool_discovery"]
        assert len(outcomes) == 1
        assert outcomes[0].status == StartupCheckStatus.WARNING

    @pytest.mark.asyncio
    async def test_tool_definitions_ok_when_clean(self) -> None:
        """Clean result produces OK outcome."""
        ctx = _make_startup_ctx(tool_definitions_strict=False)
        discovery_result = MagicMock(registry=None, findings=[], unreachable=[])
        pipeline, exc = await _run_check_services(
            ctx,
            McpToolDiscoveryService=MagicMock(
                return_value=MagicMock(
                    discover_all=AsyncMock(return_value=discovery_result)
                )
            ),
        )
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "mcp_tool_discovery"]
        assert outcomes == [
            StartupCheckOutcome("mcp_tool_discovery", StartupCheckStatus.OK)
        ]

    @pytest.mark.asyncio
    async def test_readiness_fatal_via_production_mode_raise(self) -> None:
        """FATAL is produced via the production_mode raise + generic except catch."""
        ctx = _make_startup_ctx()
        pipeline, exc = await _run_check_services(
            ctx,
            check_readiness=AsyncMock(
                side_effect=RuntimeError(
                    "Startup readiness check failed (required services unavailable): llm: unreachable"
                )
            ),
        )
        assert exc is not None
        outcomes = [o for o in pipeline.outcomes if o.source == "readiness"]
        assert len(outcomes) == 1
        assert outcomes[0].status == StartupCheckStatus.FATAL
        assert outcomes[0].message.startswith("Readiness check failed:")

    @pytest.mark.asyncio
    async def test_readiness_warning_when_issues_and_not_production(self) -> None:
        """WARNING when issues exist but production_mode is False."""
        ctx = _make_startup_ctx()
        result = HealthCheckResult(
            warnings=[
                ServiceWarning(
                    label="llm", url="http://x/health", message="llm unreachable"
                )
            ]
        )
        pipeline, exc = await _run_check_services(
            ctx, check_readiness=AsyncMock(return_value=result)
        )
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "readiness"]
        assert any(o.status == StartupCheckStatus.WARNING for o in outcomes)
        assert not any(o.status == StartupCheckStatus.FATAL for o in outcomes)

    @pytest.mark.asyncio
    async def test_readiness_ok_when_no_issues(self) -> None:
        """OK when no issues detected."""
        ctx = _make_startup_ctx()
        pipeline, exc = await _run_check_services(
            ctx, check_readiness=AsyncMock(return_value=HealthCheckResult())
        )
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "readiness"]
        assert outcomes == [StartupCheckOutcome("readiness", StartupCheckStatus.OK)]
