"""tests/agent/test_startup_approval_recovery.py

Behavior-lock tests for agent/startup.py: StartupOrchestrator._recover_pending_approvals().
"""

from __future__ import annotations

import asyncio
import subprocess
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.startup import (
    StartupInterrupted,
    StartupOrchestrator,
)
from agent.startup_mcp_starter import RETRY_DELAY_SEC
from agent.workflow.approval_ops import request_approval
from agent.workflow.state_store import StateStore
from agent.workflow.task_ops import create_task, update_task_status
from db.config import DbConfig
from db.create_schema import create_workflow_schema
from shared.mcp_config import (
    McpServerConfig,
    SecurityProfile,
    StartupMode,
    TransportType,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_startup(
    mcp_servers: dict[str, McpServerConfig],
    security_profile: SecurityProfile = SecurityProfile.PRODUCTION,
    shutdown_event: asyncio.Event | None = None,
) -> StartupOrchestrator:
    """Return a StartupOrchestrator with mocked ctx/view for _start_servers() tests."""
    ctx = MagicMock()
    ctx.cfg.mcp.security_profile = security_profile
    ctx.cfg.mcp.mcp_servers = mcp_servers
    ctx.cfg.obs.audit_log_file = "/opt/llm/logs/audit.log"
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
        auth_token="test-token",
        startup_mode=StartupMode.SUBPROCESS,
        cmd=["echo", "hello"],
    )


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


# ── StartupOrchestrator._start_servers ────────────────────────────────────────


class TestStartupOrchestratorStartServers:
    """Tests for StartupOrchestrator._start_servers()."""

    @pytest.mark.asyncio
    async def test_http_subprocess_calls_lifecycle(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup(
            {"web": cfg}, security_profile=SecurityProfile.PRODUCTION
        )

        await startup._start_servers()

        startup._ctx.services_required.lifecycle.start_http_subprocess.assert_called_once_with(
            "web", cfg, shutdown_event=None
        )

    @pytest.mark.asyncio
    async def test_http_subprocess_failure_raises_in_production(self) -> None:
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
        startup = _make_startup(
            {"web": cfg}, security_profile=SecurityProfile.PRODUCTION
        )
        retried_proc = MagicMock(spec=subprocess.Popen)
        startup._ctx.services_required.lifecycle.start_http_subprocess = AsyncMock(
            side_effect=[RuntimeError("port busy"), retried_proc]
        )

        result = await startup._start_servers()

        assert result == [retried_proc]

    @pytest.mark.asyncio
    async def test_no_process_returned_does_not_append(self) -> None:
        """start_http_subprocess() returning None (e.g. server already running)
        must not be treated as a spawned process."""
        cfg = _http_subprocess_cfg()
        startup = _make_startup(
            {"web": cfg}, security_profile=SecurityProfile.PRODUCTION
        )
        startup._ctx.services_required.lifecycle.start_http_subprocess = AsyncMock(
            return_value=None
        )

        result = await startup._start_servers()

        assert result == []

    @pytest.mark.asyncio
    async def test_pre_set_shutdown_event_stops_before_second_server(self) -> None:
        """A shutdown_event set before _start_servers() is called must stop the
        per-server loop's pre-loop check before any further server is started."""
        cfg = _http_subprocess_cfg()
        shutdown_event = asyncio.Event()
        shutdown_event.set()
        startup = _make_startup(
            {"first": cfg, "second": cfg},
            security_profile=SecurityProfile.PRODUCTION,
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
        promptly, well before RETRY_DELAY_SEC elapses."""
        cfg = _http_subprocess_cfg()
        shutdown_event = asyncio.Event()
        startup = _make_startup(
            {"web": cfg},
            security_profile=SecurityProfile.PRODUCTION,
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

        assert elapsed < RETRY_DELAY_SEC / 2

    @pytest.mark.asyncio
    async def test_shutdown_event_passed_but_never_set_is_no_op(self) -> None:
        """A real, never-set shutdown_event must not change _start_servers()
        behavior relative to shutdown_event=None."""
        cfg = _http_subprocess_cfg()
        shutdown_event = asyncio.Event()
        startup = _make_startup(
            {"web": cfg},
            security_profile=SecurityProfile.PRODUCTION,
            shutdown_event=shutdown_event,
        )

        result = await startup._start_servers()

        startup._ctx.services_required.lifecycle.start_http_subprocess.assert_called_once_with(
            "web", cfg, shutdown_event=shutdown_event
        )
        assert len(result) == 1


# ── StartupOrchestrator._verify_mcp_health ────────────────────────────────────


class TestStartupVerifyMcpHealth:
    """Tests for StartupOrchestrator._verify_mcp_health()."""

    @pytest.mark.asyncio
    async def test_health_check_passes_for_all_servers(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup(
            {"web": cfg}, security_profile=SecurityProfile.PRODUCTION
        )

        mock_resp = _make_http_mock(200)
        mock_client = _AsyncClientMock(get_return=mock_resp)

        with patch(
            "agent.startup_mcp_starter.httpx.AsyncClient", return_value=mock_client
        ):
            await startup._verify_mcp_health()

    @pytest.mark.asyncio
    async def test_health_check_failure_production_raises(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup(
            {"web": cfg}, security_profile=SecurityProfile.PRODUCTION
        )

        mock_resp_fail = _make_http_mock(503)

        with patch(
            "agent.startup_mcp_starter.httpx.AsyncClient",
            return_value=_AsyncClientMock(get_return=mock_resp_fail),
        ):
            with pytest.raises(RuntimeError, match=r"\[fatal\]"):
                await startup._verify_mcp_health()

    @pytest.mark.asyncio
    async def test_health_check_passes_after_retry(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup(
            {"web": cfg}, security_profile=SecurityProfile.PRODUCTION
        )

        mock_resp_fail = _make_http_mock(503)
        mock_resp_ok = _make_http_mock(200)

        call_count = [0]

        def client_factory(*_args, **_kwargs: object) -> _AsyncClientMock:
            call_count[0] += 1
            if call_count[0] == 1:
                return _AsyncClientMock(get_return=mock_resp_fail)
            return _AsyncClientMock(get_return=mock_resp_ok)

        with patch(
            "agent.startup_mcp_starter.httpx.AsyncClient", side_effect=client_factory
        ):
            await startup._verify_mcp_health()

        startup._view.write_warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_skips_non_subprocess_servers(self) -> None:
        cfg_persistent = McpServerConfig(
            transport=TransportType.HTTP,
            url="http://127.0.0.1:8888",
            startup_mode=StartupMode.PERSISTENT,
            cmd=["echo", "persistent"],
            auth_token="test-token",
        )
        startup = _make_startup(
            {"persistent": cfg_persistent}, security_profile=SecurityProfile.PRODUCTION
        )

        with patch("agent.startup_mcp_starter.httpx.AsyncClient") as MockClient:
            await startup._verify_mcp_health()

        MockClient.assert_not_called()

    @pytest.mark.asyncio
    async def test_tools_service_none_raises(self) -> None:
        cfg = _http_subprocess_cfg()
        ctx = MagicMock()
        ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION
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
        ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION
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
            security_profile=SecurityProfile.PRODUCTION,
            shutdown_event=shutdown_event,
        )
        mock_resp_fail = _make_http_mock(503)

        async def _fire_shutdown() -> None:
            await asyncio.sleep(0.05)
            shutdown_event.set()

        fire_task = asyncio.ensure_future(_fire_shutdown())
        start = time.monotonic()
        with patch(
            "agent.startup_mcp_starter.httpx.AsyncClient",
            return_value=_AsyncClientMock(get_return=mock_resp_fail),
        ):
            with pytest.raises(StartupInterrupted):
                await startup._verify_mcp_health()
        elapsed = time.monotonic() - start
        await fire_task

        assert elapsed < RETRY_DELAY_SEC / 2


# ── StartupOrchestrator._recover_pending_approvals ────────────────────────────────


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

        mock_store = MagicMock()

        with (
            patch(
                "agent.workflow.approval_ops.find_all_pending_approvals",
                return_value=[("task-456", approval)],
            ),
            patch("agent.workflow.state_store.StateStore", return_value=mock_store),
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

        mock_store = MagicMock()

        with (
            patch(
                "agent.workflow.approval_ops.find_all_pending_approvals",
                return_value=[("task-new", approval2), ("task-old", approval1)],
            ),
            patch("agent.workflow.state_store.StateStore", return_value=mock_store),
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

        mock_store = MagicMock()

        with (
            patch(
                "agent.workflow.approval_ops.find_all_pending_approvals",
                return_value=[
                    ("task-third", approval3),
                    ("task-second", approval2),
                    ("task-first", approval1),
                ],
            ),
            patch("agent.workflow.state_store.StateStore", return_value=mock_store),
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

        mock_store = MagicMock()

        with (
            patch(
                "agent.workflow.approval_ops.find_all_pending_approvals",
                return_value=[("task-456", approval)],
            ),
            patch("agent.workflow.state_store.StateStore", return_value=mock_store),
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

        mock_store = MagicMock()

        with (
            patch(
                "agent.workflow.approval_ops.find_all_pending_approvals",
                return_value=[("task-456", approval)],
            ),
            patch("agent.workflow.state_store.StateStore", return_value=mock_store),
        ):
            with patch("shared.logger.Logger") as mock_logger:
                await startup._recover_pending_approvals()

        assert ctx.turn.pending_approval_task_id == "task-456"
        overwrite_calls = [
            call_args
            for call_args in mock_logger.return_value.warning.call_args_list
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

        mock_store = MagicMock()

        with (
            patch(
                "agent.workflow.approval_ops.find_all_pending_approvals",
                return_value=[("task-456", approval)],
            ),
            patch("agent.workflow.state_store.StateStore", return_value=mock_store),
        ):
            with patch("shared.logger.Logger") as mock_logger:
                await startup._recover_pending_approvals()

        assert ctx.turn.pending_approval_task_id == "task-456"
        overwrite_calls = [
            call_args
            for call_args in mock_logger.return_value.warning.call_args_list
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

        mock_store = MagicMock()

        with (
            patch(
                "agent.workflow.approval_ops.find_all_pending_approvals",
                return_value=[],
            ),
            patch("agent.workflow.state_store.StateStore", return_value=mock_store),
        ):
            await startup._recover_pending_approvals()

        assert ctx.workflow.approval_pending is False
        assert ctx.turn.pending_approval_id is None
        view.write_warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_recover_pending_approvals_against_real_db_no_attribute_error(
        self, tmp_path
    ) -> None:
        """Regression: find_all_pending_approvals() must not raise AttributeError
        on sqlite3.Row.get() when a real pending approval exists in workflow.sqlite."""
        db_path = tmp_path / "workflow.sqlite"
        rag_path = tmp_path / "rag.sqlite"
        session_path = tmp_path / "session.sqlite"
        eventbus_path = tmp_path / "eventbus.sqlite"
        cfg = DbConfig(
            rag_db_path=str(rag_path),
            session_db_path=str(session_path),
            workflow_db_path=str(db_path),
            eventbus_db_path=str(eventbus_path),
        )
        with patch("db.helper.build_db_config", return_value=cfg):
            create_workflow_schema()
            store = StateStore()
            task = create_task(store._db, "sess-1", 1, "1.0.0", "wf-test-1")
            update_task_status(store._db, task.task_id, "pending_approval")
            request_approval(store._db, task_id=task.task_id, workflow_id="wf-test-1")
            store.close()

            ctx = MagicMock()
            ctx.workflow = MagicMock()
            ctx.workflow.approval_pending = False
            ctx.turn = MagicMock()
            ctx.turn.pending_approval_id = None
            ctx.turn.pending_approval_task_id = None
            view = MagicMock()

            startup = StartupOrchestrator(ctx, view)
            await startup._recover_pending_approvals()

        assert ctx.workflow.approval_pending is True
        assert ctx.turn.pending_approval_id is not None
        assert ctx.turn.pending_approval_task_id == task.task_id

    @pytest.mark.asyncio
    async def test_recover_pending_approvals_store_closed_on_exception(self) -> None:
        """store.close() is called even when find_latest_pending_approval raises."""
        ctx = MagicMock()
        ctx.workflow = MagicMock()
        view = MagicMock()

        startup = StartupOrchestrator(ctx, view)

        mock_store = MagicMock()

        with patch("agent.workflow.state_store.StateStore", return_value=mock_store):
            with patch(
                "agent.workflow.approval_ops.find_all_pending_approvals",
                side_effect=RuntimeError("db error"),
            ):
                with pytest.raises(RuntimeError, match="db error"):
                    await startup._recover_pending_approvals()

        mock_store.close.assert_called_once()
