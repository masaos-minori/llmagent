"""tests/agent/commands/test_command_blocking_offload.py

Behavior-lock tests for the `/session` maintenance offload (row 02).

Proves two contracts of running long storage calls off the event loop via
`asyncio.to_thread`:

- AC-3 (loop responsiveness): a concurrent coroutine on the same loop advances while a
  long storage callable is blocked, so the REPL stays responsive.
- AC-5 (completion semantics): cancelling/abandoning the await does not stop the
  offloaded callable, which runs to completion.
"""

from __future__ import annotations

import asyncio
import threading
from collections.abc import Callable
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from agent.commands.cmd_session import _SessionMixin


def _make_cmd() -> _SessionMixin:
    """Build a bare ``_SessionMixin`` like ``test_agent_cmd_session.py``.

    Only the attributes the maintenance dispatch path touches are wired up:
    ``_ctx``, ``_title_gen``, and ``_db_session_ops``.
    """

    session = MagicMock()
    session.session_id = 1
    session.list_sessions.return_value = []
    session.delete_session.return_value = True
    session.is_title_pending.return_value = False
    ctx = SimpleNamespace(
        session=session,
        conv=SimpleNamespace(history=[], llm_url=""),
        cfg=SimpleNamespace(llm=SimpleNamespace(context_char_limit=8000)),
        services=SimpleNamespace(
            hist_mgr=MagicMock(),
            llm=MagicMock(),
            http=MagicMock(),
            audit_logger=MagicMock(),
        ),
    )
    ctx.services_required = ctx.services  # alias for AgentContext.services_required
    cmd = object.__new__(_SessionMixin)
    cmd._ctx = ctx  # type: ignore[assignment]  # — bare object.__new__ harness injects a SimpleNamespace stub where MixinBase declares _ctx as AgentContext
    from agent.commands.session_title import SessionTitleGen

    cmd._title_gen = SessionTitleGen(ctx, cmd._out)  # type: ignore[arg-type]  # — bare object.__new__ harness passes a SimpleNamespace stub instead of a real AgentContext
    from agent.commands.db_session_ops import DbSessionOps

    cmd._db_session_ops = DbSessionOps(ctx, cmd._out)  # type: ignore[arg-type]  # — bare object.__new__ harness passes a SimpleNamespace stub instead of a real AgentContext
    return cmd


def _block_on_events() -> tuple[
    threading.Event, threading.Event, threading.Event, Callable[[], None]
]:
    """Return (started, release, completed) events for a blocking storage stub."""
    started = threading.Event()
    release = threading.Event()
    completed = threading.Event()

    def blocking_vacuum() -> None:
        started.set()
        release.wait()
        completed.set()

    return started, release, completed, blocking_vacuum


class TestCmdSessionBlockingOffload:
    @pytest.mark.asyncio
    async def test_loop_advances_while_storage_runs(self) -> None:
        """AC-3: the loop keeps yielding while the storage call runs off-loop."""
        started, release, _completed, blocking_vacuum = _block_on_events()

        cmd = _make_cmd()
        with patch(
            "agent.commands.db_session_ops.DbMaintenanceService"
        ) as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.vacuum.side_effect = blocking_vacuum
            mock_svc_cls.return_value = mock_svc

            task = asyncio.create_task(cmd._cmd_session("vacuum"))
            # Wait until the worker has entered its block; the loop is now free.
            await asyncio.to_thread(started.wait)

            # If the storage call held the loop, these yields could not complete.
            progress = 0
            for _ in range(200):
                await asyncio.sleep(0)
                progress += 1
            assert progress == 200, "event loop did not advance while storage ran"

            release.set()
            await task

    @pytest.mark.asyncio
    async def test_await_cancel_does_not_stop_work(self) -> None:
        """AC-5: cancelling the await does not stop the offloaded callable."""
        started, release, completed, blocking_vacuum = _block_on_events()

        cmd = _make_cmd()
        with patch(
            "agent.commands.db_session_ops.DbMaintenanceService"
        ) as mock_svc_cls:
            mock_svc = MagicMock()
            mock_svc.vacuum.side_effect = blocking_vacuum
            mock_svc_cls.return_value = mock_svc

            task = asyncio.create_task(cmd._cmd_session("vacuum"))
            await asyncio.to_thread(started.wait)
            # Abandon the await; the worker thread must keep running.
            task.cancel()
            with pytest.raises(asyncio.CancelledError):
                await task

            release.set()
            assert completed.wait(timeout=5) is True
