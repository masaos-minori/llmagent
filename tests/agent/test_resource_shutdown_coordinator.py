"""tests/agent/test_resource_shutdown_coordinator.py

Regression tests for ResourceShutdownCoordinator.close_resources()'s settlement-block
removal: a healthy shutdown must complete promptly (REQ-001), and no
shutdown_timeout/shutdown_error entries may be recorded once the block is removed
(REQ-002).
"""

from __future__ import annotations

import asyncio
import sqlite3
import threading
import time
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import agent.resource_shutdown_coordinator as coordinator_module
import pytest
from agent.context import TurnState
from agent.conversation_state_manager import ConversationStateManager
from agent.http_lifecycle_errors import TerminationOutcome
from agent.resource_shutdown_coordinator import ResourceShutdownCoordinator
from agent.wal_checkpoint_manager import WalCheckpointManager
from db.helper import SQLiteHelper as RealHelper
from db.models import WalCheckpointCounts


def _make_coordinator() -> ResourceShutdownCoordinator:
    ctx = MagicMock()
    ctx.services = None
    view = MagicMock()
    wal = MagicMock()
    wal.checkpoint_sync = AsyncMock(return_value=(True, []))
    wal.backup_sync = AsyncMock(return_value=("", []))
    return ResourceShutdownCoordinator(ctx, view, wal)


async def _long_running_first_turn(_line: str) -> str:
    """A stand-in for ``_generate_session_title``: pending long enough to be cancelled."""
    await asyncio.sleep(30)
    return "stubbed-title"


async def _register_first_turn_task(ctx: MagicMock) -> set[asyncio.Task[object]]:
    """Register one real first-turn task through the real producer."""
    manager = ConversationStateManager(
        ctx,
        tasks=ctx.turn.background_tasks,
        on_discard=lambda _task: None,
        on_first_turn=_long_running_first_turn,
    )
    await manager.append_user_message("first")
    return ctx.turn.background_tasks


def _registry_ctx() -> MagicMock:
    """A MagicMock ctx with a real TurnState registry and the minimal conv/stats/session
    stubs that ``append_user_message`` touches."""
    ctx = MagicMock()
    ctx.services = None
    ctx.conv = MagicMock()
    ctx.conv.system_prompt_content = ""  # skip sync_system_prompt's validation branch
    ctx.conv.append_message = AsyncMock()
    ctx.stats = MagicMock()
    ctx.stats.stat_turns = 0  # append increments to 1, firing the first-turn branch
    ctx.session = MagicMock()
    ctx.turn = TurnState()  # real, empty background_tasks set
    # append_user_message() persists through the turn's atomic boundary (SEQ-06);
    # give this non-turn test an awaitable stand-in handle.
    ctx.turn.persistence_boundary = AsyncMock()
    return ctx


class TestSettlementBlockRemoved:
    """Regression tests for the removed unconditional settlement-block sleep."""

    @pytest.mark.asyncio
    async def test_healthy_shutdown_completes_promptly(self) -> None:
        """A healthy shutdown (no pending tasks, checkpoint/backup succeed
        immediately) completes well under the shutdown bound.

        Exercises stubbed ``checkpoint_sync``/``backup_sync`` (AsyncMock): it documents the
        ordering contract, not the real blocking step (see TestRealContendedStepIsBounded).
        """
        coordinator = _make_coordinator()
        start = time.monotonic()
        await coordinator.close_resources()
        elapsed = time.monotonic() - start
        assert elapsed < 1.0

    @pytest.mark.asyncio
    async def test_no_shutdown_error_entries_after_settlement_block_removal(
        self,
    ) -> None:
        """No shutdown_timeout/shutdown_error entries are recorded — the
        settlement block that used to produce them no longer exists.

        Exercises stubbed ``checkpoint_sync``/``backup_sync`` (AsyncMock): it documents the
        error-collection contract, not the real blocking step.
        """
        coordinator = _make_coordinator()
        with patch("agent.resource_shutdown_coordinator.logger") as mock_logger:
            await coordinator.close_resources()
        error_messages = [str(c.args) for c in mock_logger.error.call_args_list]
        assert not any("shutdown_timeout" in msg for msg in error_messages)
        assert not any("shutdown_error" in msg for msg in error_messages)


class TestHttpTerminationReported:
    """Servers whose exit was not confirmed enter the shutdown error list."""

    @staticmethod
    def _coordinator_with_services(
        unconfirmed: list[tuple[str, TerminationOutcome]],
    ) -> ResourceShutdownCoordinator:
        coordinator = _make_coordinator()
        svc = MagicMock()
        svc.lifecycle.shutdown_all = AsyncMock(return_value=unconfirmed)
        svc.http.aclose = AsyncMock()
        coordinator._ctx.services = svc
        return coordinator

    @pytest.mark.asyncio
    async def test_each_unconfirmed_server_is_one_http_termination_entry(self) -> None:
        coordinator = self._coordinator_with_services(
            [
                ("a", TerminationOutcome.EXIT_UNCONFIRMED),
                ("b", TerminationOutcome.SIGNAL_NOT_DELIVERED),
            ]
        )

        await coordinator.close_resources()

        warning = coordinator._view.write_warning.call_args[0][0]
        assert warning.count("http_termination") == 2
        assert "a (exit_unconfirmed)" in warning
        assert "b (signal_not_delivered)" in warning
        # The other steps still ran.
        coordinator._ctx.services.http.aclose.assert_awaited_once()
        coordinator._wal.checkpoint_sync.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_clean_shutdown_adds_no_entry(self) -> None:
        coordinator = self._coordinator_with_services([])

        await coordinator.close_resources()

        coordinator._view.write_warning.assert_not_called()


class TestSelectiveTaskCancellation:
    """Real tasks in a real registry: only tracked background tasks are cancelled at shutdown."""

    @pytest.mark.asyncio
    async def test_only_tracked_background_tasks_cancelled(self) -> None:
        """A task registered through the real producer is cancelled, joined, and released."""
        ctx = _registry_ctx()
        view = MagicMock()
        wal = MagicMock()
        wal.checkpoint_sync = AsyncMock(return_value=(True, []))
        wal.backup_sync = AsyncMock(return_value=("", []))

        tasks = await _register_first_turn_task(ctx)
        assert len(tasks) == 1
        (running,) = tuple(tasks)

        coordinator = ResourceShutdownCoordinator(ctx, view, wal)
        await coordinator.close_resources()

        assert running.cancelled() is True
        assert running.done() is True
        assert ctx.turn.background_tasks == set()
        view.write_warning.assert_not_called()  # no "Resource close errors" for a clean cancellation

    @pytest.mark.asyncio
    async def test_empty_registry_cancels_nothing_and_raises_nothing(self) -> None:
        """An empty registry leaves shutdown intact (replaces the deleted-guard test)."""
        ctx = _registry_ctx()  # registry intentionally empty
        view = MagicMock()
        wal = MagicMock()
        wal.checkpoint_sync = AsyncMock(return_value=(True, []))
        wal.backup_sync = AsyncMock(return_value=("", []))

        coordinator = ResourceShutdownCoordinator(ctx, view, wal)
        await coordinator.close_resources()  # must not raise

        assert ctx.turn.background_tasks == set()
        view.write_warning.assert_not_called()

    @pytest.mark.asyncio
    async def test_critical_operations_not_cancelled(self) -> None:
        """Untracked work (WAL checkpoint, history write) is not cancelled; the registry empties."""
        ctx = _registry_ctx()
        view = MagicMock()
        wal = MagicMock()
        wal.checkpoint_sync = AsyncMock(return_value=(True, []))
        wal.backup_sync = AsyncMock(return_value=("", []))

        coordinator = ResourceShutdownCoordinator(ctx, view, wal)
        await coordinator.close_resources()

        assert (
            ctx.turn.background_tasks == set()
        )  # nothing was registered, nothing remains
        view.write_history.assert_called()  # the history write still ran


class TestRealContendedStepIsBounded:
    """The unstubbed counterpart of the stub-based cases above.

    A real WalCheckpointManager runs against a real WAL database held by a reader, so its
    step body genuinely blocks; the coordinator's own wait_for must abandon it and still
    run the later cleanup steps.
    """

    @pytest.mark.asyncio
    async def test_contended_checkpoint_is_abandoned_and_cleanup_still_runs(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        path = tmp_path / "session.db"
        writer = sqlite3.connect(path, isolation_level=None)
        writer.execute("PRAGMA journal_mode=WAL")
        writer.execute("PRAGMA wal_autocheckpoint=0")
        writer.execute("CREATE TABLE t (v INTEGER)")
        writer.execute("PRAGMA wal_checkpoint(TRUNCATE)")
        reader = sqlite3.connect(path, isolation_level=None)
        reader.execute("BEGIN")
        reader.execute("SELECT count(*) FROM t").fetchone()
        for i in range(20):
            writer.execute("INSERT INTO t VALUES (?)", (i,))
        closed = threading.Event()

        class _Helper(RealHelper):
            def checkpoint(self, mode: str = "TRUNCATE") -> WalCheckpointCounts:
                if mode == "PASSIVE":
                    raise sqlite3.OperationalError("database is locked")
                return super().checkpoint(mode)

            def close(self) -> None:
                super().close()
                closed.set()

        ctx = MagicMock()
        ctx.cfg.approval.allowed_root = str(tmp_path)
        ctx.session.session_id = 1
        ctx.services = None
        background = asyncio.ensure_future(asyncio.sleep(30))
        ctx.turn.background_tasks = {background}
        view = MagicMock()
        monkeypatch.setattr(coordinator_module, "_SHUTDOWN_TIMEOUT_S", 0.3)
        coordinator = ResourceShutdownCoordinator(ctx, view, WalCheckpointManager(ctx))
        try:
            with patch(
                "agent.wal_checkpoint_manager.SQLiteHelper",
                lambda *_a, **_k: _Helper(
                    db_path=str(path), sqlite_busy_timeout_ms=3000
                ),
            ):
                await coordinator.close_resources()
        finally:
            reader.close()
            await asyncio.to_thread(closed.wait, 15)
            writer.close()

        summary = view.write_warning.call_args.args[0]
        assert "wal_checkpoint_timeout" in summary
        assert "bound of 0.3s expired" in summary
        assert background.cancelled()
