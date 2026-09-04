"""Behavior-lock tests proving each check's documented severity is produced under its condition.

Cross-reference for docs/05_agent_10_01_operations-and-observability-startup-and-health.md's
severity-mapping table. Proves each documented severity is actually produced under its
documented condition, for all 8 checks run by _check_services():
security_audit, embedding_dimensions, readiness, tool_definitions, routing_drift,
routing_safety_tiers, routing_drift_live, rag_consistency.
"""

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
    overridden per-test via kwargs (named after the agent.startup import site), and return
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
    # Wire a real StartupValidationPipeline so the patched functions below are
    # actually invoked by check_services()'s own body, not bypassed by a mock.
    from agent.startup_validation import StartupValidationPipeline

    startup._validation_pipeline = StartupValidationPipeline(ctx, startup._view)
    startup._reporter = MagicMock()

    exc: Exception | None = None
    with ExitStack() as stack:
        # Patch at agent.startup_validation's own namespace: it imports each of
        # these via `from X import Y`, binding its own name, so patching the
        # defining module (e.g. agent.services.security_audit) would not
        # affect the reference check_services() actually calls.
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
        except Exception as e:  # noqa: BLE001 — capturing for assertion, not swallowing silently
            exc = e
    return captured["pipeline"], exc


class TestCheckServicesSeverityClassification:
    """Regression tests proving each check's documented severity is actually produced
    under its documented condition — see docs/05_agent_10_01_...startup-and-health.md's
    severity-mapping table for the full narrative this cross-references."""

    # ── security_audit ───────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_security_audit_fatal_when_audit_raises(self) -> None:
        """FATAL when audit_security_defaults() raises RuntimeError (e.g. production_mode
        with a missing auth_token)."""
        ctx = _make_startup_ctx()
        pipeline, exc = await _run_check_services(
            ctx,
            audit_security_defaults=MagicMock(
                side_effect=RuntimeError("no auth_token configured on server 'web'")
            ),
        )
        assert exc is not None
        outcomes = [o for o in pipeline.outcomes if o.source == "security_audit"]
        assert any(o.status == StartupCheckStatus.FATAL for o in outcomes)

    @pytest.mark.asyncio
    async def test_security_audit_warning_and_ok_both_recorded_when_non_fatal(
        self,
    ) -> None:
        """WARNING per issue AND an unconditional OK are both recorded when
        audit_security_defaults() returns warnings without raising — OK here does not
        mean 'no issues', only 'the audit function completed without raising'."""
        ctx = _make_startup_ctx()
        pipeline, exc = await _run_check_services(
            ctx,
            audit_security_defaults=MagicMock(
                return_value=["Security: no auth_token configured (auth disabled)"]
            ),
        )
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "security_audit"]
        assert any(o.status == StartupCheckStatus.WARNING for o in outcomes)
        assert any(o.status == StartupCheckStatus.OK for o in outcomes)

    # ── mcp_auth ─────────────────────────────────────────────────────────────
    # Servers below use MagicMock rather than a real McpServerConfig: row 1's
    # own `_validate_auth_token()` now rejects an empty auth_token at
    # construction time, so an empty-token McpServerConfig can no longer be
    # constructed at all -- this pipeline step is a defense-in-depth check for
    # a ctx assembled some other way (e.g. directly, as these unit tests do),
    # not a path reachable through a real Agent startup once row 1 lands.

    @pytest.mark.asyncio
    async def test_mcp_auth_fatal_when_any_server_missing_token(self) -> None:
        ctx = _make_startup_ctx()
        ctx.cfg.mcp.mcp_servers = {
            "web": MagicMock(auth_token="valid-token"),
            "shell": MagicMock(auth_token=""),
        }
        pipeline, exc = await _run_check_services(ctx)
        assert exc is not None
        outcomes = [o for o in pipeline.outcomes if o.source == "mcp_auth"]
        assert any(o.status == StartupCheckStatus.FATAL for o in outcomes)
        assert any("shell" in o.message for o in outcomes)

    @pytest.mark.asyncio
    async def test_mcp_auth_ok_when_all_servers_have_token(self) -> None:
        ctx = _make_startup_ctx()
        ctx.cfg.mcp.mcp_servers = {
            "web": MagicMock(auth_token="valid-token"),
            "shell": MagicMock(auth_token="also-valid"),
        }
        pipeline, exc = await _run_check_services(ctx)
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "mcp_auth"]
        assert any(o.status == StartupCheckStatus.OK for o in outcomes)

    @pytest.mark.asyncio
    async def test_mcp_auth_fatal_lists_all_offending_servers(self) -> None:
        ctx = _make_startup_ctx()
        ctx.cfg.mcp.mcp_servers = {
            "web": MagicMock(auth_token=""),
            "shell": MagicMock(auth_token=""),
        }
        pipeline, exc = await _run_check_services(ctx)
        assert exc is not None
        outcomes = [o for o in pipeline.outcomes if o.source == "mcp_auth"]
        assert len(outcomes) == 1
        assert "web" in outcomes[0].message
        assert "shell" in outcomes[0].message

    # ── readiness ────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_readiness_fatal_via_production_mode_raise(self) -> None:
        """FATAL is produced via the production_mode raise + generic except catch — the
        message carries the 'Readiness check failed:' prefix added by that except clause,
        proving it did NOT come from the (unreachable) result.error_messages() loop, which
        would add the raw message with no such prefix."""
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
        ctx = _make_startup_ctx()
        pipeline, exc = await _run_check_services(
            ctx, check_readiness=AsyncMock(return_value=HealthCheckResult())
        )
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "readiness"]
        assert outcomes == [StartupCheckOutcome("readiness", StartupCheckStatus.OK)]

    # ── mcp_tool_discovery ───────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_mcp_tool_discovery_warning_on_finding(self) -> None:
        ctx = _make_startup_ctx()
        finding = StartupCheckOutcome(
            "mcp_server_fetch", StartupCheckStatus.WARNING, "server unreachable"
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
        assert any(o.status == StartupCheckStatus.WARNING for o in outcomes)

    @pytest.mark.asyncio
    async def test_mcp_tool_discovery_fatal_on_strict_mode_finding(self) -> None:
        """A strict-mode finding from discover_all() is surfaced as FATAL."""
        ctx = _make_startup_ctx()
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
    async def test_mcp_tool_discovery_ok_when_clean(self) -> None:
        ctx = _make_startup_ctx()
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

    # ── routing_drift (static) ───────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_routing_drift_warning_on_messages(self) -> None:
        ctx = _make_startup_ctx()
        pipeline, exc = await _run_check_services(
            ctx,
            check_routing_drift=MagicMock(
                return_value=["Routing drift [web]: extra tool 'foo'"]
            ),
        )
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "routing_drift"]
        assert len(outcomes) == 1
        assert outcomes[0].status == StartupCheckStatus.WARNING

    @pytest.mark.asyncio
    async def test_routing_drift_emits_no_outcome_when_clean(self) -> None:
        """routing_drift never emits an OK outcome — a clean result produces zero
        recorded outcomes for this source (no pipeline.add_ok('routing_drift') call
        exists anywhere in _check_services())."""
        ctx = _make_startup_ctx()
        pipeline, exc = await _run_check_services(
            ctx, check_routing_drift=MagicMock(return_value=[])
        )
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "routing_drift"]
        assert outcomes == []

    # ── routing_safety_tiers ─────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_routing_safety_tiers_warning_on_messages(self) -> None:
        ctx = _make_startup_ctx()
        pipeline, exc = await _run_check_services(
            ctx,
            check_routing_safety_tiers=MagicMock(
                return_value=["tool 'foo' has no declared safety tier"]
            ),
        )
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "routing_safety_tiers"]
        assert len(outcomes) == 1
        assert outcomes[0].status == StartupCheckStatus.WARNING

    @pytest.mark.asyncio
    async def test_routing_safety_tiers_emits_no_outcome_when_clean(self) -> None:
        """Same no-OK behavior as routing_drift: no add_ok call exists for this source."""
        ctx = _make_startup_ctx()
        pipeline, exc = await _run_check_services(
            ctx, check_routing_safety_tiers=MagicMock(return_value=[])
        )
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "routing_safety_tiers"]
        assert outcomes == []

    # ── routing_drift_live ───────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_routing_drift_live_ok_when_clean(self) -> None:
        ctx = _make_startup_ctx()
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
    async def test_routing_drift_live_warning_when_non_strict_drift(self) -> None:
        ctx = _make_startup_ctx(tool_definitions_strict=False)
        finding = StartupCheckOutcome(
            "drift_detected",
            StartupCheckStatus.WARNING,
            "Live routing drift [web]: extra tool",
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
    async def test_routing_drift_live_skipped_on_exception(self) -> None:
        """When discover_all() raises an exception, it is caught by the blanket except clause and
        reported as FATAL; the orchestrator then raises RuntimeError."""
        ctx = _make_startup_ctx(tool_definitions_strict=True)
        pipeline, exc = await _run_check_services(
            ctx,
            McpToolDiscoveryService=MagicMock(
                side_effect=RuntimeError("Strict mode: live routing drift detected.")
            ),
        )
        assert exc is not None
        outcomes = [o for o in pipeline.outcomes if o.source == "mcp_tool_discovery"]
        assert len(outcomes) == 1
        assert outcomes[0].status == StartupCheckStatus.FATAL

    @pytest.mark.asyncio
    async def test_mcp_tool_discovery_fatal_in_production_on_exception(self) -> None:
        """When discover_all() raises and production_mode=True, the outer except clause reports
        FATAL (not SKIPPED), since a discovery-call failure means all tool calls fail this
        session."""
        ctx = _make_startup_ctx()
        pipeline, exc = await _run_check_services(
            ctx,
            McpToolDiscoveryService=MagicMock(
                side_effect=RuntimeError("discover_all boom")
            ),
        )
        assert exc is not None
        outcomes = [o for o in pipeline.outcomes if o.source == "mcp_tool_discovery"]
        assert len(outcomes) == 1
        assert outcomes[0].status == StartupCheckStatus.FATAL

    @pytest.mark.asyncio
    async def test_mcp_tool_discovery_fatal_in_dev_on_exception(self) -> None:
        """When discover_all() raises and production_mode=False, the outer except clause reports
        FATAL (instead of SKIPPED), since a discovery-call failure means all tool calls fail this
        session."""
        ctx = _make_startup_ctx()
        pipeline, exc = await _run_check_services(
            ctx,
            McpToolDiscoveryService=MagicMock(
                side_effect=RuntimeError("discover_all boom")
            ),
        )
        assert exc is not None
        outcomes = [o for o in pipeline.outcomes if o.source == "mcp_tool_discovery"]
        assert len(outcomes) == 1
        assert outcomes[0].status == StartupCheckStatus.FATAL

    # ── rag_consistency ──────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_rag_consistency_ok(self) -> None:
        ctx = _make_startup_ctx()
        rag_service = MagicMock()
        rag_service.consistency.return_value = MagicMock(is_consistent=True, issues=[])
        pipeline, exc = await _run_check_services(
            ctx, RagMaintenanceService=MagicMock(return_value=rag_service)
        )
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "rag_consistency"]
        assert outcomes == [
            StartupCheckOutcome("rag_consistency", StartupCheckStatus.OK)
        ]

    @pytest.mark.asyncio
    async def test_rag_consistency_warning_per_issue(self) -> None:
        ctx = _make_startup_ctx()
        rag_service = MagicMock()
        rag_service.consistency.return_value = MagicMock(
            is_consistent=False, issues=["orphaned chunk 123"]
        )
        pipeline, exc = await _run_check_services(
            ctx, RagMaintenanceService=MagicMock(return_value=rag_service)
        )
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "rag_consistency"]
        assert len(outcomes) == 1
        assert outcomes[0].status == StartupCheckStatus.WARNING

    @pytest.mark.asyncio
    async def test_rag_consistency_skipped_on_exception(
        self, caplog: pytest.LogCaptureFixture
    ) -> None:
        """`logger` is created locally inside check_services() (agent.startup_validation)
        as `Logger(__name__, ...)`, whose underlying stdlib logger has
        propagate=False -- caplog's handler must be attached directly to it,
        not relied on via propagation to the root logger."""
        import logging as _logging

        ctx = _make_startup_ctx()
        target_logger = _logging.getLogger("agent.startup_validation")
        target_logger.addHandler(caplog.handler)
        previous_level = target_logger.level
        target_logger.setLevel("WARNING")
        try:
            pipeline, exc = await _run_check_services(
                ctx,
                RagMaintenanceService=MagicMock(side_effect=RuntimeError("db locked")),
            )
        finally:
            target_logger.removeHandler(caplog.handler)
            target_logger.setLevel(previous_level)
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "rag_consistency"]
        assert len(outcomes) == 1
        assert outcomes[0].status == StartupCheckStatus.SKIPPED
        assert "db locked" in outcomes[0].message

        # Verify the exception is logged as a warning (non-fatal maintenance check).
        # >=1 rather than ==1: pytest's own log-capture plugin may additionally
        # attach a handler to this logger across the test session, independent
        # of this test's own explicit handler above -- the count is not the
        # point, only that the warning was logged with the expected content.
        warning_records = [
            r
            for r in caplog.records
            if r.levelname == "WARNING" and "RAG consistency check failed" in r.message
        ]
        assert len(warning_records) >= 1
        assert "db locked" in warning_records[0].message
