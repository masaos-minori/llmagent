"""tests/test_startup.py
Behavior-lock tests for agent/startup.py: StartupOrchestrator._start_servers().

Migrated from TestStartSubprocessServers in tests/test_repl.py when
_start_subprocess_servers was moved to StartupOrchestrator._start_servers().
"""

from __future__ import annotations

import asyncio
import sqlite3
import subprocess
import time
from contextlib import ExitStack
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.context import ConversationState
from agent.shared.health_models import (
    HealthCheckResult,
    ServiceWarning,
    StartupCheckOutcome,
    StartupCheckStatus,
    StartupValidationResult,
)
from agent.startup import (
    HEALTH_CHECK_RETRY_DELAY_SEC,
    StartupInterrupted,
    StartupOrchestrator,
)
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
    shutdown_event: asyncio.Event | None = None,
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
    return StartupOrchestrator(ctx, view, shutdown_event=shutdown_event)


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
            "web", cfg, shutdown_event=None
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

    @pytest.mark.asyncio
    async def test_retry_success_appends_to_spawned_subprocesses(self) -> None:
        """A retry-success (first attempt raises, retry returns a Popen) must append
        the retried proc onto self._spawned_subprocesses, not just the first-attempt
        success path."""
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg}, security_profile=SecurityProfile.LOCAL)
        retried_proc = MagicMock(spec=subprocess.Popen)
        startup._ctx.services_required.lifecycle.start_http_subprocess = AsyncMock(
            side_effect=[RuntimeError("port busy"), retried_proc]
        )

        result = await startup._start_servers()

        assert result == [retried_proc]
        assert startup._spawned_subprocesses == [retried_proc]

    @pytest.mark.asyncio
    async def test_pre_set_shutdown_event_stops_before_second_server(self) -> None:
        """A shutdown_event set before _start_servers() is called must stop the
        per-server loop's pre-loop check before any further server is started."""
        cfg = _http_subprocess_cfg()
        shutdown_event = asyncio.Event()
        shutdown_event.set()
        startup = _make_startup(
            {"first": cfg, "second": cfg},
            security_profile=SecurityProfile.LOCAL,
            shutdown_event=shutdown_event,
        )

        with pytest.raises(StartupInterrupted):
            await startup._start_servers()

        assert (
            startup._ctx.services_required.lifecycle.start_http_subprocess.call_count
            <= 1
        )

    @pytest.mark.asyncio
    async def test_shutdown_event_during_retry_delay_raises_promptly(self) -> None:
        """shutdown_event firing mid-retry-delay must interrupt _interruptible_sleep()
        promptly, well before HEALTH_CHECK_RETRY_DELAY_SEC elapses."""
        cfg = _http_subprocess_cfg()
        shutdown_event = asyncio.Event()
        startup = _make_startup(
            {"web": cfg},
            security_profile=SecurityProfile.LOCAL,
            shutdown_event=shutdown_event,
        )
        startup._ctx.services_required.lifecycle.start_http_subprocess.side_effect = (
            RuntimeError("port busy")
        )

        async def _fire_shutdown() -> None:
            await asyncio.sleep(0.05)
            shutdown_event.set()

        fire_task = asyncio.ensure_future(_fire_shutdown())
        start = time.monotonic()
        with pytest.raises(StartupInterrupted):
            await startup._start_servers()
        elapsed = time.monotonic() - start
        await fire_task

        assert elapsed < HEALTH_CHECK_RETRY_DELAY_SEC / 2

    @pytest.mark.asyncio
    async def test_shutdown_event_passed_but_never_set_is_no_op(self) -> None:
        """A real, never-set shutdown_event must not change _start_servers()
        behavior relative to shutdown_event=None."""
        cfg = _http_subprocess_cfg()
        shutdown_event = asyncio.Event()
        startup = _make_startup(
            {"web": cfg},
            security_profile=SecurityProfile.LOCAL,
            shutdown_event=shutdown_event,
        )

        result = await startup._start_servers()

        startup._ctx.services_required.lifecycle.start_http_subprocess.assert_called_once_with(
            "web", cfg, shutdown_event=shutdown_event
        )
        assert result == startup._spawned_subprocesses


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
            return_value=[("task-new", approval2), ("task-old", approval1)],
        ):
            await startup._recover_pending_approvals()

        assert ctx.workflow.approval_pending is True
        assert ctx.turn.pending_approval_id == "approval-new"
        assert ctx.turn.pending_approval_task_id == "task-new"
        assert len(view.write_warning.call_args[0][0]) > 0

    @pytest.mark.asyncio
    async def test_startup_recovery_selects_newest_not_oldest_pending_approval(
        self,
    ) -> None:
        """Regression: _recover_pending_approvals must select newest, not oldest.

        This test fails against the pre-fix code path (results[-1]).
        """
        ctx = MagicMock()
        ctx.workflow = MagicMock()
        ctx.workflow.approval_pending = False
        ctx.turn = MagicMock()
        ctx.turn.pending_approval_id = None
        view = MagicMock()

        startup = StartupOrchestrator(ctx, view)

        approval1 = MagicMock()
        approval1.approval_id = "approval-first"
        approval1.reason = "first reason"

        approval2 = MagicMock()
        approval2.approval_id = "approval-second"
        approval2.reason = "second reason"

        approval3 = MagicMock()
        approval3.approval_id = "approval-third"
        approval3.reason = "third reason"

        with patch(
            "agent.startup.find_all_pending_approvals",
            return_value=[
                ("task-third", approval3),
                ("task-second", approval2),
                ("task-first", approval1),
            ],
        ):
            await startup._recover_pending_approvals()

        assert ctx.workflow.approval_pending is True
        assert ctx.turn.pending_approval_id == "approval-third"
        assert ctx.turn.pending_approval_task_id == "task-third"

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
    async def test_startup_recovery_warns_on_pending_approval_task_id_overwrite(
        self,
    ) -> None:
        """Recovery logs a warning when it overwrites an already-set pending_approval_task_id."""
        ctx = MagicMock()
        ctx.workflow = MagicMock()
        ctx.workflow.approval_pending = False
        ctx.turn = MagicMock()
        ctx.turn.pending_approval_id = None
        ctx.turn.pending_approval_task_id = "task-old"
        view = MagicMock()

        startup = StartupOrchestrator(ctx, view)

        approval = MagicMock()
        approval.approval_id = "approval-123"
        approval.reason = "waiting for deploy"

        with patch(
            "agent.startup.find_all_pending_approvals",
            return_value=[("task-456", approval)],
        ):
            with patch("agent.startup.logger") as mock_logger:
                await startup._recover_pending_approvals()

        assert ctx.turn.pending_approval_task_id == "task-456"
        overwrite_calls = [
            call_args
            for call_args in mock_logger.warning.call_args_list
            if "Overwriting pending_approval_task_id" in call_args[0][0]
        ]
        assert len(overwrite_calls) == 1
        assert overwrite_calls[0][0][1] == "task-old"
        assert overwrite_calls[0][0][2] == "task-456"

    @pytest.mark.asyncio
    async def test_startup_recovery_no_warning_when_task_id_not_already_set(
        self,
    ) -> None:
        """No overwrite warning is logged when pending_approval_task_id starts unset."""
        ctx = MagicMock()
        ctx.workflow = MagicMock()
        ctx.workflow.approval_pending = False
        ctx.turn = MagicMock()
        ctx.turn.pending_approval_id = None
        ctx.turn.pending_approval_task_id = None
        view = MagicMock()

        startup = StartupOrchestrator(ctx, view)

        approval = MagicMock()
        approval.approval_id = "approval-123"
        approval.reason = "waiting for deploy"

        with patch(
            "agent.startup.find_all_pending_approvals",
            return_value=[("task-456", approval)],
        ):
            with patch("agent.startup.logger") as mock_logger:
                await startup._recover_pending_approvals()

        assert ctx.turn.pending_approval_task_id == "task-456"
        overwrite_calls = [
            call_args
            for call_args in mock_logger.warning.call_args_list
            if "Overwriting pending_approval_task_id" in call_args[0][0]
        ]
        assert not overwrite_calls

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
        # Bind the real ConversationState.append_message/extend_messages/
        # replace_history so _setup_prompt()'s ctx.conv.replace_history(...)
        # call actually mutates ctx.conv.history, instead of being swallowed
        # as a no-op MagicMock call.
        ctx.conv.append_message = ConversationState.append_message.__get__(ctx.conv)
        ctx.conv.extend_messages = ConversationState.extend_messages.__get__(ctx.conv)
        ctx.conv.replace_history = ConversationState.replace_history.__get__(ctx.conv)
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

        assert "--- USER MEMORY ---" in ctx.conv.system_prompt_content
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
        # Bind the real ConversationState.append_message/extend_messages/
        # replace_history so _setup_prompt()'s ctx.conv.replace_history(...)
        # call actually mutates ctx.conv.history, instead of being swallowed
        # as a no-op MagicMock call.
        ctx.conv.append_message = ConversationState.append_message.__get__(ctx.conv)
        ctx.conv.extend_messages = ConversationState.extend_messages.__get__(ctx.conv)
        ctx.conv.replace_history = ConversationState.replace_history.__get__(ctx.conv)
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

        assert "--- USER MEMORY ---" in ctx.conv.system_prompt_content
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
    async def test_rollback_on_start_servers_failure(self) -> None:
        orch, mock_lifecycle = _make_rollback_startup()
        orch._start_servers = AsyncMock(side_effect=RuntimeError("server start failed"))
        orch._check_services = AsyncMock()

        with pytest.raises(RuntimeError, match="server start failed"):
            await orch.run()

        mock_lifecycle.shutdown_all.assert_awaited_once()

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "security_profile",
        [SecurityProfile.PRODUCTION, SecurityProfile.LOCAL],
    )
    async def test_rollback_on_partial_multi_server_failure(
        self, security_profile: SecurityProfile
    ) -> None:
        """run() rolls back via shutdown_all() after a two-server startup where the
        first server starts successfully and the second fails on both the first
        attempt and the retry.

        In PRODUCTION, the second server's retry failure makes `_start_servers()`
        itself raise mid-loop (after `first_proc` was already appended). In a
        non-production profile, `_start_servers()` swallows the retry failure and
        returns normally with only `first_proc` recorded, so `_check_services()` is
        mocked to fail instead to drive `run()` into its rollback path — both cases
        exercise "one subprocess already started before the failure that triggers
        rollback" from the plan's Goal.
        """
        ctx = MagicMock()
        ctx.cfg.mcp.security_profile = security_profile
        ctx.cfg.mcp.mcp_servers = {
            "first": _http_subprocess_cfg(),
            "second": _http_subprocess_cfg(),
        }
        ctx.services_required.tools = MagicMock()
        mock_lifecycle = AsyncMock()
        ctx.services_required.lifecycle = mock_lifecycle
        first_proc = MagicMock(spec=subprocess.Popen)
        mock_lifecycle.start_http_subprocess = AsyncMock(
            side_effect=[
                first_proc,
                RuntimeError("port busy"),
                RuntimeError("port busy"),
            ]
        )
        view = MagicMock()
        orch = StartupOrchestrator(ctx, view)
        orch._initialize = MagicMock()
        orch._check_services = AsyncMock(side_effect=RuntimeError("downstream failure"))
        orch._recover_pending_approvals = AsyncMock()
        orch._setup_prompt = AsyncMock()

        with pytest.raises(RuntimeError):
            await orch.run()

        mock_lifecycle.shutdown_all.assert_awaited_once()
        assert orch._spawned_subprocesses == [first_proc]

    @pytest.mark.asyncio
    async def test_rollback_no_op_when_no_subprocess_started(self) -> None:
        """run() still rolls back (safe no-op shutdown_all()) when _start_servers()
        raises before any subprocess is spawned."""
        orch, mock_lifecycle = _make_rollback_startup()
        orch._start_servers = AsyncMock(
            side_effect=RuntimeError("no servers configured")
        )
        orch._check_services = AsyncMock()

        with pytest.raises(RuntimeError, match="no servers configured"):
            await orch.run()

        mock_lifecycle.shutdown_all.assert_awaited_once()
        assert orch._spawned_subprocesses == []

    @pytest.mark.asyncio
    async def test_run_populates_spawned_subprocesses_on_exception_path(self) -> None:
        """Regression: _spawned_subprocesses must be populated even when run() raises."""
        orch, mock_lifecycle = _make_rollback_startup()
        fake_procs = [
            MagicMock(spec=subprocess.Popen),
            MagicMock(spec=subprocess.Popen),
        ]
        orch._start_servers = AsyncMock(return_value=fake_procs)
        orch._check_services = AsyncMock(
            side_effect=RuntimeError("health check failed")
        )
        orch._recover_pending_approvals = AsyncMock()
        orch._setup_prompt = AsyncMock()
        mock_lifecycle.shutdown_all.side_effect = OSError("shutdown failed")

        with pytest.raises(RuntimeError, match="health check failed"):
            await orch.run()

        assert orch._spawned_subprocesses == fake_procs

    @pytest.mark.asyncio
    async def test_run_returns_spawned_subprocesses_on_success(self) -> None:
        """Assert run()'s third return value equals the real spawned-process list."""
        orch, mock_lifecycle = _make_rollback_startup()
        fake_procs = [
            MagicMock(spec=subprocess.Popen),
            MagicMock(spec=subprocess.Popen),
        ]
        orch._start_servers = AsyncMock(return_value=fake_procs)
        orch._check_services = AsyncMock()
        orch._recover_pending_approvals = AsyncMock()
        orch._setup_prompt = AsyncMock()
        orch._cmds = MagicMock()
        orch._orchestrator = MagicMock()

        cmds, orchestrator, spawned = await orch.run()

        assert spawned == fake_procs

    @pytest.mark.asyncio
    async def test_startup_interrupted_triggers_rollback_like_any_other_exception(
        self,
    ) -> None:
        """StartupInterrupted must flow through run()'s existing rollback
        `except Exception as setup_err:` block unchanged — no dedicated branch."""
        orch, mock_lifecycle = _make_rollback_startup()
        orch._start_servers = AsyncMock(
            side_effect=StartupInterrupted("shutdown requested")
        )

        with pytest.raises(StartupInterrupted, match="shutdown requested"):
            await orch.run()

        mock_lifecycle.shutdown_all.assert_awaited_once()


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

    @pytest.mark.asyncio
    async def test_mcp_tool_discovery_fatal_in_dev_on_exception(self) -> None:
        """When discover_all() raises and production_mode=False, the outer except clause reports
        FATAL (instead of SKIPPED), since a discovery-call failure means all tool calls fail this
        session."""
        ctx = _make_startup_ctx(production_mode=False)
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
        with patch("agent.startup.logger") as mock_logger:
            pipeline, exc = await _run_check_services(
                ctx,
                RagMaintenanceService=MagicMock(
                    side_effect=RuntimeError("db locked")
                ),
            )
        assert exc is None
        outcomes = [o for o in pipeline.outcomes if o.source == "rag_consistency"]
        assert len(outcomes) == 1
        assert outcomes[0].status == StartupCheckStatus.SKIPPED
        assert "db locked" in outcomes[0].message

        # Verify the exception is logged as a warning (non-fatal maintenance check).
        warning_calls = [
            call_args
            for call_args in mock_logger.warning.call_args_list
            if "RAG consistency check failed" in call_args[0][0]
        ]
        assert len(warning_calls) == 1
        assert "db locked" in str(warning_calls[0][0][1])


# ── Helpers for _verify_mcp_health tests ──────────────────────────────────────


class _AsyncClientMock:
    """Minimal async context manager that mimics httpx.AsyncClient."""

    def __init__(
        self, get_return: MagicMock | None = None, timeout: float = 5.0
    ) -> None:
        self._get_return = get_return
        self.timeout = timeout

    async def __aenter__(self) -> _AsyncClientMock:
        return self

    async def __aexit__(self, *args: object, **kwargs: object) -> None:
        pass

    async def get(self, url: str, **_kw: object) -> MagicMock:
        assert self._get_return is not None
        return self._get_return


def _make_http_mock(resp_status: int) -> MagicMock:
    resp = MagicMock()
    resp.status_code = resp_status
    return resp


# ── StartupOrchestrator._verify_mcp_health ────────────────────────────────────


class TestStartupVerifyMcpHealth:
    """Tests for StartupOrchestrator._verify_mcp_health()."""

    @pytest.mark.asyncio
    async def test_health_check_passes_for_all_servers(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg}, security_profile=SecurityProfile.LOCAL)

        mock_resp = _make_http_mock(200)
        mock_client = _AsyncClientMock(get_return=mock_resp)

        with patch("agent.startup.httpx.AsyncClient", return_value=mock_client):
            await startup._verify_mcp_health()

    @pytest.mark.asyncio
    async def test_health_check_failure_non_production_warns(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg}, security_profile=SecurityProfile.LOCAL)

        mock_resp_fail = _make_http_mock(503)

        def client_factory(*_args, **_kwargs: object) -> _AsyncClientMock:
            return _AsyncClientMock(get_return=mock_resp_fail)

        with patch("agent.startup.httpx.AsyncClient", side_effect=client_factory):
            await startup._verify_mcp_health()

        startup._view.write_warning.assert_called_once()

    @pytest.mark.asyncio
    async def test_health_check_failure_production_raises(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup(
            {"web": cfg}, security_profile=SecurityProfile.PRODUCTION
        )

        mock_resp_fail = _make_http_mock(503)

        with patch(
            "agent.startup.httpx.AsyncClient",
            return_value=_AsyncClientMock(get_return=mock_resp_fail),
        ):
            with pytest.raises(RuntimeError, match=r"\[fatal\]"):
                await startup._verify_mcp_health()

    @pytest.mark.asyncio
    async def test_health_check_passes_after_retry(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg}, security_profile=SecurityProfile.LOCAL)

        mock_resp_fail = _make_http_mock(503)
        mock_resp_ok = _make_http_mock(200)

        call_count = [0]

        def client_factory(*_args, **_kwargs: object) -> _AsyncClientMock:
            call_count[0] += 1
            if call_count[0] == 1:
                return _AsyncClientMock(get_return=mock_resp_fail)
            return _AsyncClientMock(get_return=mock_resp_ok)

        with patch("agent.startup.httpx.AsyncClient", side_effect=client_factory):
            await startup._verify_mcp_health()

        startup._view.write_warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_non_subprocess_servers(self) -> None:
        cfg_persistent = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:8888",
            startup_mode=StartupMode.PERSISTENT,
            cmd=["echo", "persistent"],
        )
        startup = _make_startup(
            {"persistent": cfg_persistent}, security_profile=SecurityProfile.LOCAL
        )

        with patch("agent.startup.httpx.AsyncClient") as MockClient:
            await startup._verify_mcp_health()

        MockClient.assert_not_called()

    @pytest.mark.asyncio
    async def test_tools_service_none_raises(self) -> None:
        cfg = _http_subprocess_cfg()
        ctx = MagicMock()
        ctx.cfg.mcp.security_profile = SecurityProfile.LOCAL
        ctx.cfg.mcp.mcp_servers = {"web": cfg}
        ctx.services_required.tools = None
        ctx.services_required.lifecycle = AsyncMock()
        view = MagicMock()
        startup = StartupOrchestrator(ctx, view)

        with pytest.raises(RuntimeError, match="tools service not initialized"):
            await startup._verify_mcp_health()

    @pytest.mark.asyncio
    async def test_lifecycle_service_none_raises(self) -> None:
        cfg = _http_subprocess_cfg()
        ctx = MagicMock()
        ctx.cfg.mcp.security_profile = SecurityProfile.LOCAL
        ctx.cfg.mcp.mcp_servers = {"web": cfg}
        ctx.services_required.tools = MagicMock()
        ctx.services_required.lifecycle = None
        view = MagicMock()
        startup = StartupOrchestrator(ctx, view)

        with pytest.raises(RuntimeError, match="lifecycle service not initialized"):
            await startup._verify_mcp_health()

    @pytest.mark.asyncio
    async def test_shutdown_event_during_health_retry_delay_raises_promptly(
        self,
    ) -> None:
        """shutdown_event firing mid-health-retry-delay must interrupt
        _interruptible_sleep() promptly, mirroring the _start_servers() retry-delay
        interruption behavior."""
        cfg = _http_subprocess_cfg()
        shutdown_event = asyncio.Event()
        startup = _make_startup(
            {"web": cfg},
            security_profile=SecurityProfile.LOCAL,
            shutdown_event=shutdown_event,
        )
        mock_resp_fail = _make_http_mock(503)

        async def _fire_shutdown() -> None:
            await asyncio.sleep(0.05)
            shutdown_event.set()

        fire_task = asyncio.ensure_future(_fire_shutdown())
        start = time.monotonic()
        with patch(
            "agent.startup.httpx.AsyncClient",
            return_value=_AsyncClientMock(get_return=mock_resp_fail),
        ):
            with pytest.raises(StartupInterrupted):
                await startup._verify_mcp_health()
        elapsed = time.monotonic() - start
        await fire_task

        assert elapsed < HEALTH_CHECK_RETRY_DELAY_SEC / 2


# ── StartupOrchestrator._setup_prompt() memory failure ─────────────────────────


class TestStartupMemoryFailures:
    """Tests for StartupOrchestrator._setup_prompt() categorized logging on memory failure."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "exception_class, log_method, exception_msg",
        [
            (sqlite3.Error, "error", "database error"),
            (ConnectionError, "warning", "connection refused"),
            (ValueError, "info", "invalid value"),
        ],
    )
    async def test_memory_injection_categorized_logging(
        self, exception_class, log_method, exception_msg
    ) -> None:
        ctx = MagicMock()
        ctx.conv.system_prompt_name = "default"
        ctx.cfg.tool.system_prompts = {"default": "Initial prompt"}
        ctx.cfg.agent_memory_max_startup_snippets = 10
        ctx.session.session_id = "test-session"
        ctx.conv.memory_disabled = False

        mock_mem = MagicMock()
        mock_mem.on_session_start.side_effect = exception_class(exception_msg)
        ctx.services_required.memory = mock_mem

        view = MagicMock()
        startup = StartupOrchestrator(ctx, view)

        with patch("agent.startup.logger") as mock_logger:
            await startup._setup_prompt()

        assert ctx.conv.memory_disabled is True

        # Verify correct log level was used
        log_func = getattr(mock_logger, log_method)
        log_func.assert_called_once()

        # Check if message contains the expected part
        args, _ = log_func.call_args
        assert "Memory injection failed during startup" in args[0]
        assert exception_msg in str(args[1]) if len(args) > 1 else ""

        # Verify view.write_warning was called
        view.write_warning.assert_called_once()
        warn_msg = str(view.write_warning.call_args[0][0])
        assert "Memory injection failed" in warn_msg
        assert exception_msg in warn_msg
