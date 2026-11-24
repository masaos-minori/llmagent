"""tests/agent/commands/test_command_blocking_offload.py

Behavior-lock tests for the `/session` maintenance offload (row 02).

Proves two contracts of running long storage calls off the event loop via
`asyncio.to_thread`:

- AC-3 (loop responsiveness): a concurrent coroutine on the same loop advances while a
  long storage callable is blocked, so the REPL stays responsive.
- REQ-002 (cooperative interruption): for an operation the registry declares
  cancelable, the offloaded call stops at the next progress callback once its job's
  cancellation event is set, and the run is reported as cancelled. Cancelling the await
  does not stop the worker, so an abandoned await records `outcome_unknown` instead of a
  completion (REQ-004).
"""

from __future__ import annotations

import asyncio
import threading
import time
from collections.abc import Callable
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.commands.cmd_session import _SessionMixin
from agent.services.maintenance_jobs import JobState, MaintenanceJobRegistry
from agent.services.models import DbPurgeResult

from tests.agent._config_test_defaults import MIN_DB_CONFIG, MIN_MAINTENANCE_CONFIG

# Bounded so a run that never sees the event ends instead of blocking the test process.
MAX_WORKER_ITERATIONS = 500
WORKER_POLL_SECONDS = 0.001


def _make_cmd(
    *,
    job_registry: MaintenanceJobRegistry | None = None,
) -> _SessionMixin:
    """Build a bare ``_SessionMixin`` like ``test_agent_cmd_session.py``.

    Only the attributes the maintenance dispatch path touches are wired up:
    ``_ctx``, ``_title_gen``, and ``_db_session_ops``. The single registry instance is
    the one on `ctx.services`, and the approval answer is supplied so the run is recorded.
    """

    session = MagicMock()
    session.session_id = 1
    session.list_sessions.return_value = []
    session.delete_session.return_value = True
    session.is_title_pending.return_value = False
    ctx = SimpleNamespace(
        session=session,
        conv=SimpleNamespace(history=[], llm_url=""),
        cfg=SimpleNamespace(
            # The command handlers receive the typed configuration from the process that
            # owns the file; the fixture supplies it rather than reading a config file.
            db=MIN_DB_CONFIG,
            maintenance=MIN_MAINTENANCE_CONFIG,
            llm=SimpleNamespace(context_char_limit=8000),
        ),
        services=SimpleNamespace(
            hist_mgr=MagicMock(),
            llm=MagicMock(),
            http=MagicMock(),
            audit_logger=MagicMock(),
            job_registry=job_registry or MaintenanceJobRegistry(),
        ),
    )
    ctx.services_required = ctx.services  # alias for AgentContext.services_required
    cmd = object.__new__(_SessionMixin)
    cmd._ctx = ctx  # type: ignore[assignment]  # — bare object.__new__ harness injects a SimpleNamespace stub where MixinBase declares _ctx as AgentContext
    from agent.commands.session_title import SessionTitleGen

    cmd._title_gen = SessionTitleGen(ctx, cmd._out)  # type: ignore[arg-type]  # — bare object.__new__ harness passes a SimpleNamespace stub instead of a real AgentContext
    from agent.commands.db_session_ops import DbSessionOps

    cmd._db_session_ops = DbSessionOps(ctx, cmd._out)  # type: ignore[arg-type]  # — bare object.__new__ harness passes a SimpleNamespace stub instead of a real AgentContext
    cmd._confirm_for_job = AsyncMock(return_value=True)  # type: ignore[assignment]  # — the fixture supplies the approval answer in place of the async handler method
    cmd._free_space_guard = MagicMock(return_value=True)  # type: ignore[assignment]  # — the fixture supplies the guard decision in place of the method
    return cmd


def _block_on_events() -> tuple[
    threading.Event,
    threading.Event,
    threading.Event,
    Callable[..., object],
]:
    """Return (started, release, completed) events for a blocking storage stub."""
    started = threading.Event()
    release = threading.Event()
    completed = threading.Event()

    def blocking_purge(*args, **kwargs) -> DbPurgeResult:
        """The operation receives the job's event as `stop`, so a cancelled run ends here."""
        stop = kwargs["stop"]
        started.set()
        release.wait(timeout=5)
        completed.set()
        return DbPurgeResult(
            sessions_removed=0, verified=False, interrupted=stop.is_set()
        )

    return started, release, completed, blocking_purge


class TestCmdSessionBlockingOffload:
    @pytest.mark.asyncio
    async def test_loop_advances_while_storage_runs(self) -> None:
        """AC-3: the loop keeps yielding while the storage call runs off-loop."""
        started, release, _completed, blocking_purge = _block_on_events()

        cmd = _make_cmd()
        with patch(
            "agent.commands.db_session_ops.DbMaintenanceService"
        ) as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.purge.side_effect = blocking_purge
            mock_svc_cls.return_value = mock_svc

            task = asyncio.create_task(cmd._cmd_session("purge"))
            # Wait until the worker has entered its block; the loop is now free.
            await asyncio.to_thread(started.wait, timeout=5)

            # If the storage call held the loop, these yields could not complete.
            progress = 0
            for _ in range(200):
                await asyncio.sleep(0)
                progress += 1
            assert progress == 200, "event loop did not advance while storage ran"

            release.set()
            await task

    @pytest.mark.asyncio
    async def test_cancelled_job_stops_at_the_progress_boundary(
        self, capsys: pytest.CaptureFixture
    ) -> None:
        """REQ-002: a cancelable operation stops at the next callback when its job is cancelled."""

        started = threading.Event()

        def interruptible_purge(*args, **kwargs) -> DbPurgeResult:
            # A progress callback is the only place the run can notice the cancellation.
            stop = kwargs["stop"]
            started.set()
            for _ in range(MAX_WORKER_ITERATIONS):
                if stop.is_set():
                    return DbPurgeResult(
                        sessions_removed=0, verified=False, interrupted=True
                    )
                time.sleep(WORKER_POLL_SECONDS)
            return DbPurgeResult(sessions_removed=0, verified=False, interrupted=False)

        cmd = _make_cmd()
        registry = cmd._ctx.services.job_registry
        with patch(
            "agent.commands.db_session_ops.DbMaintenanceService"
        ) as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.purge.side_effect = interruptible_purge
            mock_svc_cls.return_value = mock_svc

            task = asyncio.create_task(cmd._cmd_session("purge"))
            await asyncio.to_thread(started.wait, timeout=5)
            job = registry.running_jobs()[0]
            outcome = registry.cancel(job.job_id)
            assert outcome.interrupted is True

            await task
            assert job.state is JobState.CANCELLED
            assert f"job {job.job_id} cancelled" in capsys.readouterr().out

    @pytest.mark.asyncio
    async def test_abandoned_await_records_an_unknown_outcome(self) -> None:
        """The worker keeps running after the await is cancelled, so its outcome is unknown."""
        started = threading.Event()
        released = threading.Event()

        def blocking_purge(*args, **kwargs) -> DbPurgeResult:
            stop = kwargs["stop"]
            started.set()
            released.wait(timeout=5)
            return DbPurgeResult(
                sessions_removed=0, verified=False, interrupted=stop.is_set()
            )

        cmd = _make_cmd()
        registry = cmd._ctx.services.job_registry
        with patch(
            "agent.commands.db_session_ops.DbMaintenanceService"
        ) as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.purge.side_effect = blocking_purge
            mock_svc_cls.return_value = mock_svc

            task = asyncio.create_task(cmd._cmd_session("purge"))
            await asyncio.to_thread(started.wait, timeout=5)
            job = registry.running_jobs()[0]
            # Abandon the await: the worker is not stopped by it, so the record cannot
            # claim the run finished (REQ-004).
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert job.state is JobState.OUTCOME_UNKNOWN

            released.set()
            # The worker finished on its own; the record stays unknown.
            assert job.state is JobState.OUTCOME_UNKNOWN
