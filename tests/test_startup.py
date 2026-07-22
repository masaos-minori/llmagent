"""tests/test_startup.py
Behavior-lock tests for agent/startup.py: StartupOrchestrator._start_servers().

Migrated from TestStartSubprocessServers in tests/test_repl.py when
_start_subprocess_servers was moved to StartupOrchestrator._start_servers().
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
from shared.mcp_config import (
    McpServerConfig,
    SecurityProfile,
    StartupMode,
    TransportType,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_startup(
    mcp_servers: dict[str, McpServerConfig],
    security_profile: SecurityProfile = SecurityProfile.LOCAL,
) -> StartupOrchestrator:
    """Return a StartupOrchestrator with mocked ctx/view for _start_servers() tests."""
    ctx = MagicMock()
    ctx.cfg.mcp.security_profile = security_profile
    ctx.cfg.mcp.mcp_servers = mcp_servers
    ctx.services_required.tools = MagicMock()
    ctx.services_required.tools.set_transport = MagicMock()
    ctx.services_required.lifecycle = AsyncMock()
    ctx.services_required.lifecycle.start_http_subprocess = AsyncMock()
    view = MagicMock()
    view.write_warning = MagicMock()
    return StartupOrchestrator(ctx, view)


def _http_subprocess_cfg() -> McpServerConfig:
    return McpServerConfig(
        transport=TransportType.HTTP,
        url="http://127.0.0.1:9999",
        startup_mode=StartupMode.SUBPROCESS,
        cmd=["echo", "hello"],
    )


# ── StartupOrchestrator._start_servers ────────────────────────────────────────


class TestStartupOrchestratorStartServers:
    """Tests for StartupOrchestrator._start_servers()."""

    @pytest.mark.asyncio
    async def test_http_subprocess_calls_lifecycle(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg}, security_profile=SecurityProfile.LOCAL)

        await startup._start_servers()

        startup._ctx.services_required.lifecycle.start_http_subprocess.assert_called_once_with(
            "web", cfg
        )

    @pytest.mark.asyncio
    async def test_http_subprocess_failure_is_swallowed(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg}, security_profile=SecurityProfile.LOCAL)
        startup._ctx.services_required.lifecycle.start_http_subprocess.side_effect = (
            RuntimeError("port busy")
        )

        # Must not raise; failure is logged and printed as warning
        await startup._start_servers()

    @pytest.mark.asyncio
    async def test_production_profile_raises_on_start_failure(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup(
            {"web": cfg}, security_profile=SecurityProfile.PRODUCTION
        )
        startup._ctx.services_required.lifecycle.start_http_subprocess.side_effect = (
            RuntimeError("port busy")
        )

        with pytest.raises(RuntimeError, match=r"\[fatal\]"):
            await startup._start_servers()

    @pytest.mark.asyncio
    async def test_production_failure_message_contains_server_key(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup(
            {"web": cfg}, security_profile=SecurityProfile.PRODUCTION
        )
        startup._ctx.services_required.lifecycle.start_http_subprocess.side_effect = (
            OSError("no such file")
        )

        with pytest.raises(RuntimeError) as exc_info:
            await startup._start_servers()

        assert "web" in str(exc_info.value)


# ── StartupOrchestrator._recover_pending_approvals ─────────────────────────────


class TestStartupOrchestratorRecoverPendingApprovals:
    """Tests for StartupOrchestrator._recover_pending_approvals()."""

    @pytest.mark.asyncio
    async def test_startup_recovery_restores_pending_approval(self) -> None:
        """Startup recovery restores approval_pending state from the workflow database."""
        ctx = MagicMock()
        ctx.workflow = MagicMock()
        ctx.workflow.approval_pending = False
        ctx.turn = MagicMock()
        ctx.turn.pending_approval_id = None
        view = MagicMock()

        startup = StartupOrchestrator(ctx, view)

        approval = MagicMock()
        approval.approval_id = "approval-123"
        approval.reason = "waiting for deploy"

        with patch(
            "agent.startup.find_all_pending_approvals",
            return_value=[("task-456", approval)],
        ):
            await startup._recover_pending_approvals()

        assert ctx.workflow.approval_pending is True
        assert ctx.turn.pending_approval_id == "approval-123"
        assert ctx.turn.pending_approval_task_id == "task-456"

    @pytest.mark.asyncio
    async def test_startup_recovery_shows_last_of_multiple_pending_approvals(
        self,
    ) -> None:
        """When multiple pending approvals exist, the most recent one is shown."""
        ctx = MagicMock()
        ctx.workflow = MagicMock()
        ctx.workflow.approval_pending = False
        ctx.turn = MagicMock()
        ctx.turn.pending_approval_id = None
        view = MagicMock()

        startup = StartupOrchestrator(ctx, view)

        approval1 = MagicMock()
        approval1.approval_id = "approval-old"
        approval1.reason = "old reason"

        approval2 = MagicMock()
        approval2.approval_id = "approval-new"
        approval2.reason = "new reason"

        with patch(
            "agent.startup.find_all_pending_approvals",
            return_value=[("task-old", approval1), ("task-new", approval2)],
        ):
            await startup._recover_pending_approvals()

        assert ctx.workflow.approval_pending is True
        assert ctx.turn.pending_approval_id == "approval-new"
        assert ctx.turn.pending_approval_task_id == "task-new"
        assert len(view.write_warning.call_args[0][0]) > 0

    @pytest.mark.asyncio
    async def test_startup_recovery_warning_contains_task_and_approval_id(self) -> None:
        """Startup warning includes task_id and approval_id for debugging."""
        ctx = MagicMock()
        ctx.workflow = MagicMock()
        ctx.workflow.approval_pending = False
        ctx.turn = MagicMock()
        ctx.turn.pending_approval_id = None
        view = MagicMock()

        startup = StartupOrchestrator(ctx, view)

        approval = MagicMock()
        approval.approval_id = "approval-123"
        approval.reason = "waiting for deploy"

        with patch(
            "agent.startup.find_all_pending_approvals",
            return_value=[("task-456", approval)],
        ):
            await startup._recover_pending_approvals()

        warning_calls = view.write_warning.call_args_list
        assert len(warning_calls) == 1
        warning_text = str(warning_calls[0][0][0])
        assert "task-456" in warning_text, (
            f"Expected task_id in warning, got: {warning_text}"
        )
        assert "approval-123" in warning_text, (
            f"Expected approval_id in warning, got: {warning_text}"
        )
        assert "/approve approval-123" in warning_text, (
            f"Expected /approve command with approval_id in warning, got: {warning_text}"
        )
        assert "/reject approval-123" in warning_text, (
            f"Expected /reject command with approval_id in warning, got: {warning_text}"
        )

    @pytest.mark.asyncio
    async def test_startup_recovery_no_pending_approval(self) -> None:
        """No warning or state change when there is no pending approval."""
        ctx = MagicMock()
        ctx.workflow = MagicMock()
        ctx.workflow.approval_pending = False
        ctx.turn = MagicMock()
        ctx.turn.pending_approval_id = None
        view = MagicMock()

        startup = StartupOrchestrator(ctx, view)

        with patch("agent.startup.find_all_pending_approvals", return_value=[]):
            await startup._recover_pending_approvals()

        assert ctx.workflow.approval_pending is False
        assert ctx.turn.pending_approval_id is None
        view.write_warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_recover_pending_approvals_store_closed_on_exception(self) -> None:
        """store.close() is called even when find_latest_pending_approval raises."""
        ctx = MagicMock()
        ctx.workflow = MagicMock()
        view = MagicMock()

        startup = StartupOrchestrator(ctx, view)

        mock_store = MagicMock()

        with patch("agent.startup.StateStore", return_value=mock_store):
            with patch(
                "agent.startup.find_all_pending_approvals",
                side_effect=RuntimeError("db error"),
            ):
                with pytest.raises(RuntimeError, match="db error"):
                    await startup._recover_pending_approvals()

        mock_store.close.assert_called_once()


# ── _setup_prompt() regression tests ────────────────────────────────────────────


class TestStartupOrchestratorSetupPrompt:
    """Regression tests for _setup_prompt() — pinned notes must NOT be injected."""

    @pytest.mark.asyncio
    async def test_no_pinned_notes_block_injected(self) -> None:
        """[Pinned Notes] block must NOT appear in system prompt."""
        ctx = MagicMock()
        ctx.services_required.memory = None  # memory disabled
        ctx.conv.system_prompt_name = "default"
        ctx.cfg.tool.system_prompts = {"default": "Initial prompt"}
        view = MagicMock()
        startup = StartupOrchestrator(ctx, view)

        await startup._setup_prompt()

        assert "[Pinned Notes]" not in ctx.conv.system_prompt_content
        assert ctx.conv.history == [{"role": "system", "content": "Initial prompt"}]

    @pytest.mark.asyncio
    async def test_memory_snippets_are_injected_when_enabled(self) -> None:
        """Memory snippets ARE injected when memory is enabled."""
        snippet = MagicMock()
        snippet.text = "test memory"
        ctx = MagicMock()
        mock_mem = MagicMock()
        mock_mem.on_session_start.return_value = [snippet]
        ctx.services_required.memory = mock_mem
        ctx.session.session_id = 1
        ctx.conv.system_prompt_name = "default"
        ctx.cfg.tool.system_prompts = {"default": "Initial prompt"}
        ctx.cfg.agent_memory_max_startup_snippets = 10
        view = MagicMock()
        startup = StartupOrchestrator(ctx, view)

        await startup._setup_prompt()

        assert "[Relevant memories]" in ctx.conv.system_prompt_content
        assert "test memory" in ctx.conv.system_prompt_content

    @pytest.mark.asyncio
    async def test_no_memory_injection_when_disabled(self) -> None:
        """System prompt is unchanged when memory is disabled."""
        ctx = MagicMock()
        ctx.services_required.memory = None
        ctx.conv.system_prompt_name = "default"
        ctx.cfg.tool.system_prompts = {"default": "Initial prompt"}
        view = MagicMock()
        startup = StartupOrchestrator(ctx, view)

        await startup._setup_prompt()

        assert "[Relevant memories]" not in ctx.conv.system_prompt_content
        assert ctx.conv.system_prompt_content == "Initial prompt"

    @pytest.mark.asyncio
    async def test_history_set_to_system_message(self) -> None:
        """conv.history is set to [system message] after _setup_prompt."""
        ctx = MagicMock()
        ctx.services_required.memory = None
        ctx.conv.system_prompt_name = "default"
        ctx.cfg.tool.system_prompts = {"default": "Initial prompt"}
        view = MagicMock()
        startup = StartupOrchestrator(ctx, view)

        await startup._setup_prompt()

        assert len(ctx.conv.history) == 1
        assert ctx.conv.history[0] == {"role": "system", "content": "Initial prompt"}

    @pytest.mark.asyncio
    async def test_memory_snippets_truncated_when_exceeds_limit(self) -> None:
        """Memory snippets are truncated when exceeding the configured limit."""
        snippets = [MagicMock(text=f"memory {i}") for i in range(15)]
        ctx = MagicMock()
        mock_mem = MagicMock()
        mock_mem.on_session_start.return_value = snippets
        ctx.services_required.memory = mock_mem
        ctx.session.session_id = 1
        ctx.conv.system_prompt_name = "default"
        ctx.cfg.tool.system_prompts = {"default": "Initial prompt"}
        ctx.cfg.agent_memory_max_startup_snippets = 10
        view = MagicMock()
        startup = StartupOrchestrator(ctx, view)

        await startup._setup_prompt()

        assert "[Relevant memories]" in ctx.conv.system_prompt_content
        assert "memory 9" in ctx.conv.system_prompt_content
        assert "memory 10" not in ctx.conv.system_prompt_content


# ── Workflow preflight abort tests ───────────────────────────────────────────


class TestStartupWorkflowPreflight:
    """Startup aborts (raises RuntimeError) on workflow preflight failures."""

    def _make_startup(self) -> StartupOrchestrator:
        ctx = MagicMock()
        view = MagicMock()
        return StartupOrchestrator(ctx, view)

    def test_aborts_on_missing_workflow_definition(self) -> None:
        startup = self._make_startup()
        with patch(
            "agent.startup.check_workflow_definition",
            side_effect=RuntimeError("missing workflow.json"),
        ):
            with pytest.raises(RuntimeError, match="missing workflow.json"):
                startup._check_workflow_definition()

    def test_aborts_on_invalid_workflow_json(self) -> None:
        startup = self._make_startup()
        with patch(
            "agent.startup.check_workflow_definition",
            side_effect=RuntimeError("invalid JSON"),
        ):
            with pytest.raises(RuntimeError, match="invalid JSON"):
                startup._check_workflow_definition()

    def test_aborts_on_missing_workflow_schema(self) -> None:
        startup = self._make_startup()
        with patch(
            "agent.repl_health.check_workflow_schema",
            side_effect=RuntimeError("missing table: tasks"),
        ):
            with pytest.raises(RuntimeError, match="missing table"):
                startup._check_workflow_schema()

    def test_definition_check_passes_when_no_error(self) -> None:
        startup = self._make_startup()
        with patch("agent.startup.check_workflow_definition"):
            startup._check_workflow_definition()  # must not raise

    def test_schema_check_passes_when_no_error(self) -> None:
        startup = self._make_startup()
        with patch("agent.repl_health.check_workflow_schema"):
            startup._check_workflow_schema()  # must not raise

    def test_error_message_has_no_workflow_mode_suggestion(self) -> None:
        startup = self._make_startup()
        with patch(
            "agent.startup.check_workflow_definition",
            side_effect=RuntimeError("definition missing"),
        ):
            with pytest.raises(RuntimeError) as exc_info:
                startup._check_workflow_definition()
        assert "workflow_mode" not in str(exc_info.value)
        assert "disabled" not in str(exc_info.value)


# ── StartupOrchestrator.run() rollback tests ─────────────────────────────────


def _make_rollback_startup() -> tuple[StartupOrchestrator, AsyncMock]:
    """Return (orchestrator, mock_lifecycle) with _initialize patched to a no-op."""
    ctx = MagicMock()
    mock_lifecycle = AsyncMock()
    ctx.services_required.lifecycle = mock_lifecycle
    view = MagicMock()
    orch = StartupOrchestrator(ctx, view)
    orch._initialize = MagicMock()
    return orch, mock_lifecycle


class TestStartupRollback:
    """run() calls lifecycle.shutdown_all() iff _start_servers() succeeded before failure."""

    @pytest.mark.asyncio
    async def test_rollback_on_check_services_failure(self) -> None:
        orch, mock_lifecycle = _make_rollback_startup()
        orch._start_servers = AsyncMock()
        orch._check_services = AsyncMock(
            side_effect=RuntimeError("health check failed")
        )
        orch._recover_pending_approvals = AsyncMock()
        orch._setup_prompt = AsyncMock()

        with pytest.raises(RuntimeError, match="health check failed"):
            await orch.run()

        mock_lifecycle.shutdown_all.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rollback_on_recover_pending_failure(self) -> None:
        orch, mock_lifecycle = _make_rollback_startup()
        orch._start_servers = AsyncMock()
        orch._check_services = AsyncMock()
        orch._recover_pending_approvals = AsyncMock(
            side_effect=RuntimeError("approval recovery failed")
        )
        orch._setup_prompt = AsyncMock()

        with pytest.raises(RuntimeError, match="approval recovery failed"):
            await orch.run()

        mock_lifecycle.shutdown_all.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rollback_shutdown_failure_preserves_original_error(self) -> None:
        orch, mock_lifecycle = _make_rollback_startup()
        orch._start_servers = AsyncMock()
        orch._check_services = AsyncMock(side_effect=RuntimeError("original error"))
        orch._recover_pending_approvals = AsyncMock()
        orch._setup_prompt = AsyncMock()
        mock_lifecycle.shutdown_all.side_effect = OSError("shutdown failed")

        with pytest.raises(RuntimeError, match="original error"):
            await orch.run()

    @pytest.mark.asyncio
    async def test_no_rollback_on_initialize_failure(self) -> None:
        orch, mock_lifecycle = _make_rollback_startup()
        orch._initialize = MagicMock(side_effect=RuntimeError("init failed"))

        with pytest.raises(RuntimeError, match="init failed"):
            await orch.run()

        mock_lifecycle.shutdown_all.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_no_rollback_on_start_servers_failure(self) -> None:
        orch, mock_lifecycle = _make_rollback_startup()
        orch._start_servers = AsyncMock(side_effect=RuntimeError("server start failed"))
        orch._check_services = AsyncMock()

        with pytest.raises(RuntimeError, match="server start failed"):
            await orch.run()

        mock_lifecycle.shutdown_all.assert_not_awaited()


# ── StartupOrchestrator._check_services() severity classification ───────────
#
# Cross-reference for docs/05_agent_10_01_operations-and-observability-startup-and-health.md's
# severity-mapping table. Proves each documented severity is actually produced under its
# documented condition, for all 8 checks run by _check_services():
# security_audit, embedding_dimensions, readiness, tool_definitions, routing_drift,
# routing_safety_tiers, routing_drift_live, rag_consistency.


def _make_startup_ctx(
    *,
    production_mode: bool = False,
    memory_embed_dim: int = 768,
    tool_definitions_strict: bool = False,
) -> MagicMock:
    """Return a ctx MagicMock configured for _check_services() tests."""
    ctx = MagicMock()
    ctx.cfg.mcp.security_profile = (
        SecurityProfile.PRODUCTION if production_mode else SecurityProfile.LOCAL
    )
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
    exc: Exception | None = None
    with ExitStack() as stack:
        for name, mock_obj in mocks.items():
            stack.enter_context(patch(f"agent.startup.{name}", mock_obj))
        stack.enter_context(
            patch("agent.startup.StartupValidationResult", side_effect=_new_pipeline)
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
        ctx = _make_startup_ctx(production_mode=True)
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
        ctx = _make_startup_ctx(production_mode=False)
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

    # ── embedding_dimensions ─────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_embedding_dimensions_fatal_on_mismatch(self) -> None:
        ctx = _make_startup_ctx(memory_embed_dim=768)
        pipeline, exc = await _run_check_services(ctx, embedding_dims=384)
        assert exc is not None
        outcomes = [o for o in pipeline.outcomes if o.source == "embedding_dimensions"]
        assert outcomes == [
            StartupCheckOutcome(
                "embedding_dimensions",
                StartupCheckStatus.FATAL,
                "Embedding dimension mismatch: memory=768, db=384",
            )
        ]

    @pytest.mark.asyncio
    async def test_embedding_dimensions_ok_on_match(self) -> None:
        ctx = _make_startup_ctx(memory_embed_dim=768)
        pipeline, exc = await _run_check_services(ctx, embedding_dims=768)
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "embedding_dimensions"]
        assert outcomes == [
            StartupCheckOutcome("embedding_dimensions", StartupCheckStatus.OK)
        ]

    # ── readiness ────────────────────────────────────────────────────────────

    @pytest.mark.asyncio
    async def test_readiness_fatal_via_production_mode_raise(self) -> None:
        """FATAL is produced via the production_mode raise + generic except catch — the
        message carries the 'Readiness check failed:' prefix added by that except clause,
        proving it did NOT come from the (unreachable) result.error_messages() loop, which
        would add the raw message with no such prefix."""
        ctx = _make_startup_ctx(production_mode=True)
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
        ctx = _make_startup_ctx(production_mode=False)
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
        reported as SKIPPED."""
        ctx = _make_startup_ctx(tool_definitions_strict=True)
        pipeline, exc = await _run_check_services(
            ctx,
            McpToolDiscoveryService=MagicMock(
                side_effect=RuntimeError("Strict mode: live routing drift detected.")
            ),
        )
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "mcp_tool_discovery"]
        assert len(outcomes) == 1
        assert outcomes[0].status == StartupCheckStatus.SKIPPED

    @pytest.mark.asyncio
    async def test_mcp_tool_discovery_fatal_in_production_on_exception(self) -> None:
        """When discover_all() raises and production_mode=True, the outer except clause reports
        FATAL (not SKIPPED), since a discovery-call failure means all tool calls fail this
        session."""
        ctx = _make_startup_ctx(production_mode=True)
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
    async def test_rag_consistency_skipped_on_exception(self) -> None:
        ctx = _make_startup_ctx()
        pipeline, exc = await _run_check_services(
            ctx,
            RagMaintenanceService=MagicMock(side_effect=RuntimeError("db locked")),
        )
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "rag_consistency"]
        assert len(outcomes) == 1
        assert outcomes[0].status == StartupCheckStatus.SKIPPED
