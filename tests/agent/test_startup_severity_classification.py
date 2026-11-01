"""Behavior-lock tests proving each check's documented severity is produced under its condition.

Cross-reference for docs/23_agent/agent_10_01_operations-and-observability-startup-and-health.md's
severity-mapping table. Proves each documented severity is actually produced under its
documented condition, for the 6 pipeline sources _check_services() records:
mcp_auth, readiness, mcp_tool_discovery, routing_drift, routing_safety_tiers,
rag_consistency.
"""

from __future__ import annotations

import sqlite3
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
from db.models import ConsistencyFinding, FindingSeverity
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
    """Run StartupOrchestrator._check_services() with clean-pass mocks for all 5 patched checks,
    overridden per-test via kwargs (named after the agent.startup import site), and return
    (captured pipeline outcomes, exception raised by _check_services() or None).
    """
    consistent_rag = MagicMock()
    consistent_rag.consistency.return_value = MagicMock(is_consistent=True, issues=[])
    mocks: dict[str, object] = {
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
        # defining module (e.g. agent.services.mcp_health) would not
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
    under its documented condition — see docs/23_agent/agent_10_01_...startup-and-health.md's
    severity-mapping table for the full narrative this cross-references."""

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

    @pytest.mark.asyncio
    async def test_routing_drift_unexpected_failure_is_fatal_when_strict(self) -> None:
        """An unexpected failure of the drift check follows routing_drift_strict:
        an unknown result is not a clean result, so strict mode fails closed."""
        ctx = _make_startup_ctx()
        ctx.cfg.tool.routing_drift_strict = True
        pipeline, exc = await _run_check_services(
            ctx, check_routing_drift=MagicMock(side_effect=ValueError("boom"))
        )
        assert exc is not None
        outcomes = [o for o in pipeline.outcomes if o.source == "routing_drift"]
        assert any(o.status == StartupCheckStatus.FATAL for o in outcomes)

    @pytest.mark.asyncio
    async def test_routing_drift_unexpected_failure_is_warning_when_not_strict(
        self,
    ) -> None:
        ctx = _make_startup_ctx()
        ctx.cfg.tool.routing_drift_strict = False
        pipeline, exc = await _run_check_services(
            ctx, check_routing_drift=MagicMock(side_effect=ValueError("boom"))
        )
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "routing_drift"]
        assert len(outcomes) == 1
        assert outcomes[0].status == StartupCheckStatus.WARNING

    @pytest.mark.asyncio
    async def test_routing_drift_runtime_error_is_fatal_regardless_of_strict(
        self,
    ) -> None:
        ctx = _make_startup_ctx()
        ctx.cfg.tool.routing_drift_strict = False
        pipeline, exc = await _run_check_services(
            ctx,
            check_routing_drift=MagicMock(side_effect=RuntimeError("drift detected")),
        )
        assert exc is not None
        outcomes = [o for o in pipeline.outcomes if o.source == "routing_drift"]
        assert any(o.status == StartupCheckStatus.FATAL for o in outcomes)

    @pytest.mark.asyncio
    async def test_routing_drift_unreadable_strictness_is_fatal(self) -> None:
        """When the strictness setting cannot be read, fail closed (treat as strict)."""
        ctx = _make_startup_ctx()
        ctx.cfg.tool = MagicMock(spec=[])  # reading routing_drift_strict raises
        pipeline, exc = await _run_check_services(
            ctx, check_routing_drift=MagicMock(side_effect=ValueError("boom"))
        )
        assert exc is not None
        outcomes = [o for o in pipeline.outcomes if o.source == "routing_drift"]
        assert any(o.status == StartupCheckStatus.FATAL for o in outcomes)

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

    @pytest.mark.asyncio
    async def test_routing_safety_tiers_unexpected_failure_is_fatal(self) -> None:
        """Safety Tier failures stay Fail-Closed (INV-07), whatever the drift policy."""
        ctx = _make_startup_ctx()
        ctx.cfg.tool.routing_drift_strict = False
        pipeline, exc = await _run_check_services(
            ctx, check_routing_safety_tiers=MagicMock(side_effect=ValueError("boom"))
        )
        assert exc is not None
        outcomes = [o for o in pipeline.outcomes if o.source == "routing_safety_tiers"]
        assert any(o.status == StartupCheckStatus.FATAL for o in outcomes)

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
    async def test_rag_consistency_fatal_when_duplicate_chunk_index(self) -> None:
        """A FATAL finding (duplicate chunk_index) aborts startup regardless of any
        config — RAG severity is code-fixed (AC-4), so there is no strict variant."""
        ctx = _make_startup_ctx()
        rag_service = MagicMock()
        rag_service.consistency.return_value = MagicMock(
            is_consistent=False,
            findings=[
                ConsistencyFinding(
                    severity=FindingSeverity.FATAL,
                    message="[CRITICAL] Duplicate chunk_index detected.",
                    repair_action="restore_from_backup",
                ),
            ],
        )
        pipeline, exc = await _run_check_services(
            ctx, RagMaintenanceService=MagicMock(return_value=rag_service)
        )
        assert exc is not None
        outcomes = [o for o in pipeline.outcomes if o.source == "rag_consistency"]
        assert len(outcomes) == 1
        assert outcomes[0].status == StartupCheckStatus.FATAL
        assert "restore_from_backup" in outcomes[0].message

    @pytest.mark.asyncio
    async def test_rag_consistency_warning_when_fts_gap_only(self) -> None:
        """A DEGRADED finding (FTS gap) warns with the repair action named; it never
        aborts."""
        ctx = _make_startup_ctx()
        rag_service = MagicMock()
        rag_service.consistency.return_value = MagicMock(
            is_consistent=False,
            findings=[
                ConsistencyFinding(
                    severity=FindingSeverity.DEGRADED,
                    message="[WARNING] FTS gap detected.",
                    repair_action="rebuild_fts",
                ),
            ],
        )
        pipeline, exc = await _run_check_services(
            ctx, RagMaintenanceService=MagicMock(return_value=rag_service)
        )
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "rag_consistency"]
        assert len(outcomes) == 1
        assert outcomes[0].status == StartupCheckStatus.WARNING
        assert "rebuild_fts" in outcomes[0].message

    @pytest.mark.asyncio
    async def test_rag_consistency_unverified_warning_on_check_failure(self) -> None:
        """A check failure marks the corpus identity-unverified via a WARNING (never
        SKIPPED, never FATAL); the gate enforces fail-closed (REQ-007)."""
        ctx = _make_startup_ctx()
        rag_service = MagicMock()
        rag_service.consistency.side_effect = sqlite3.Error("db locked")
        pipeline, exc = await _run_check_services(
            ctx, RagMaintenanceService=MagicMock(return_value=rag_service)
        )
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "rag_consistency"]
        assert len(outcomes) == 1
        assert outcomes[0].status == StartupCheckStatus.WARNING
        assert "identity-unverified" in outcomes[0].message
        assert "DATABASE_OR_IO" in outcomes[0].message
