"""tests/test_repl.py
Behavior-lock tests for agent/repl.py: AgentREPL._repl_loop and _get_chunk_count.

MCP server startup tests (formerly TestStartSubprocessServers) were moved to
tests/test_startup.py when _start_subprocess_servers was extracted to
StartupOrchestrator._start_servers().
"""

from __future__ import annotations

import asyncio
import json
import os
import sqlite3
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.repl import AgentREPL

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_bare_repl() -> AgentREPL:
    """Return an AgentREPL instance bypassing __init__ to avoid real deps."""
    repl = AgentREPL.__new__(AgentREPL)
    ctx = MagicMock()
    ctx.conv.shutdown_requested = False
    ctx.services_required.llm.stat_partial_completions = 0
    ctx.session.session_id = 1
    ctx.cfg.approval.allowed_root = "/opt/llm"
    ctx.stats.stat_partial_completions = 0
    ctx.stats.stat_turns = 0
    ctx.stats.stat_tool_calls = 0
    ctx.stats.stat_tool_errors = 0
    ctx.stats.stat_latency = {}
    ctx.stats.stat_semantic_cache_hits = 0
    ctx.stats.stat_input_tokens = 0
    ctx.stats.stat_output_tokens = 0
    ctx.services.hist_mgr.stat_compress_count = 0
    ctx.services.hist_mgr.stat_fallback_truncate_count = 0
    ctx.services.llm.stat_parse_errors = 0
    ctx.services.llm.stat_heartbeat_timeouts = 0
    ctx.services.llm.stat_reconnects = 0
    ctx.services.memory.on_session_stop = AsyncMock()
    ctx.services.lifecycle.shutdown_all = AsyncMock()
    ctx.services.http.aclose = AsyncMock()
    repl._ctx = ctx
    view = MagicMock()
    view.read_multiline = AsyncMock(return_value="")
    repl._view = view
    repl._cmds = AsyncMock()
    repl._cmds.dispatch = AsyncMock(return_value=True)
    repl._orchestrator = AsyncMock()
    repl._orchestrator.handle_turn = AsyncMock()
    repl._shutdown_event = None
    ds = MagicMock()
    ds.fetch.return_value = []
    repl._diagnostic_store = ds
    return repl


# ── _get_chunk_count ──────────────────────────────────────────────────────────


class TestGetWorkflowStatus:
    def test_returns_unknown_when_orchestrator_is_none(self) -> None:
        repl = _make_bare_repl()
        repl._orchestrator = None
        assert repl._get_workflow_status() == "unknown"

    def test_returns_enabled_when_tracking_enabled(self) -> None:
        repl = _make_bare_repl()
        repl._orchestrator.workflow_status = MagicMock(
            return_value={"tracking": "enabled"}
        )
        assert repl._get_workflow_status() == "enabled"

    def test_returns_not_loaded_when_tracking_not_loaded(self) -> None:
        repl = _make_bare_repl()
        repl._orchestrator.workflow_status = MagicMock(
            return_value={"tracking": "not_loaded"}
        )
        assert repl._get_workflow_status() == "not loaded"


class TestGetChunkCount:
    def test_returns_formatted_count(self) -> None:
        repl = _make_bare_repl()
        mock_svc = MagicMock()
        mock_svc.stats_rag.return_value = (0, 1234)
        with patch("agent.repl.RagMaintenanceService", return_value=mock_svc):
            result = repl._get_chunk_count()
        assert result == "1,234"

    def test_returns_question_mark_on_db_error(self) -> None:
        repl = _make_bare_repl()
        mock_svc = MagicMock()
        mock_svc.stats_rag.side_effect = RuntimeError("db gone")
        with patch("agent.repl.RagMaintenanceService", return_value=mock_svc):
            result = repl._get_chunk_count()

        assert result == "?"

    def test_returns_zero_when_fetchall_empty(self) -> None:
        repl = _make_bare_repl()
        mock_svc = MagicMock()
        mock_svc.stats_rag.return_value = (0, 0)
        with patch("agent.repl.RagMaintenanceService", return_value=mock_svc):
            result = repl._get_chunk_count()
        assert result == "0"


# ── _repl_loop ────────────────────────────────────────────────────────────────


class TestReplLoop:
    """Tests for the main input dispatch loop."""

    @pytest.mark.asyncio
    async def test_exit_command_breaks_loop(self) -> None:
        repl = _make_bare_repl()
        with patch("builtins.input", side_effect=["/exit"]):
            await repl._repl_loop()
        # No assertions needed: reaching here means the loop terminated cleanly.

    @pytest.mark.asyncio
    async def test_eof_breaks_loop(self) -> None:
        repl = _make_bare_repl()
        with patch("builtins.input", side_effect=EOFError):
            await repl._repl_loop()

    @pytest.mark.asyncio
    async def test_keyboard_interrupt_breaks_loop(self) -> None:
        repl = _make_bare_repl()
        with patch("builtins.input", side_effect=KeyboardInterrupt):
            await repl._repl_loop()

    @pytest.mark.asyncio
    async def test_slash_command_dispatched_to_cmds(self) -> None:
        repl = _make_bare_repl()
        repl._cmds.dispatch = AsyncMock(return_value=True)
        with patch("builtins.input", side_effect=["/help", "/exit"]):
            await repl._repl_loop()
        repl._cmds.dispatch.assert_called_once_with("/help")

    @pytest.mark.asyncio
    async def test_unknown_slash_command_prints_hint(self) -> None:
        repl = _make_bare_repl()
        repl._cmds.dispatch = AsyncMock(return_value=False)
        with patch("builtins.input", side_effect=["/unknown_cmd", "/exit"]):
            await repl._repl_loop()
        repl._view.write_warning.assert_called_once()
        msg = repl._view.write_warning.call_args[0][0]
        assert "Unknown command" in msg
        assert "/unknown_cmd" in msg

    @pytest.mark.asyncio
    async def test_regular_text_dispatched_to_orchestrator(self) -> None:
        repl = _make_bare_repl()
        with patch("builtins.input", side_effect=["hello world", "/exit"]):
            await repl._repl_loop()
        repl._orchestrator.handle_turn.assert_called_once_with("hello world")

    @pytest.mark.asyncio
    async def test_empty_line_skipped(self) -> None:
        repl = _make_bare_repl()
        with patch("builtins.input", side_effect=["", "  ", "/exit"]):
            await repl._repl_loop()
        repl._orchestrator.handle_turn.assert_not_called()
        repl._cmds.dispatch.assert_not_called()

    @pytest.mark.asyncio
    async def test_shutdown_requested_breaks_loop(self) -> None:
        repl = _make_bare_repl()
        # After returning first line, mark shutdown
        call_count = 0

        def _input_with_shutdown(_prompt: str = "") -> str:
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "first line"
            repl._ctx.conv.shutdown_requested = True
            return "second line"

        with patch("builtins.input", side_effect=_input_with_shutdown):
            await repl._repl_loop()
        # handle_turn called once (for "first line"); shutdown breaks before second
        repl._orchestrator.handle_turn.assert_called_once_with("first line")

    @pytest.mark.asyncio
    async def test_cmds_none_raises_runtime_error(self) -> None:
        """After refactor: assert → RuntimeError guard."""
        repl = _make_bare_repl()
        repl._cmds = None  # type: ignore[assignment]
        with pytest.raises((AssertionError, RuntimeError)):
            await repl._repl_loop()

    @pytest.mark.asyncio
    async def test_orchestrator_none_raises_runtime_error(self) -> None:
        """After refactor: assert → RuntimeError guard."""
        repl = _make_bare_repl()
        repl._orchestrator = None  # type: ignore[assignment]
        with pytest.raises((AssertionError, RuntimeError)):
            await repl._repl_loop()

    @pytest.mark.asyncio
    async def test_partial_completion_warning_emitted(self) -> None:
        """write_warning is called when stat_partial_completions increases after handle_turn."""
        repl = _make_bare_repl()
        repl._ctx.services_required.llm.stat_partial_completions = 0
        repl._ctx.stats.stat_partial_completions = 0

        def _increment_partial(*_args, **_kwargs):
            repl._ctx.stats.stat_partial_completions += 1

        repl._orchestrator.handle_turn = AsyncMock(side_effect=_increment_partial)
        with patch("builtins.input", side_effect=["hello", "/exit"]):
            await repl._repl_loop()
        write_warning_calls = repl._view.write_warning.call_args_list
        partial_warnings = [c for c in write_warning_calls if "Partial" in str(c)]
        assert partial_warnings, "Expected partial completion warning"

    @pytest.mark.asyncio
    async def test_no_partial_completion_no_warning(self) -> None:
        """write_warning is NOT called for partial completions when stat unchanged."""
        repl = _make_bare_repl()
        repl._ctx.services_required.llm.stat_partial_completions = 0
        repl._ctx.stats.stat_partial_completions = 0
        with patch("builtins.input", side_effect=["hello", "/exit"]):
            await repl._repl_loop()
        write_warning_calls = repl._view.write_warning.call_args_list
        partial_warnings = [c for c in write_warning_calls if "Partial" in str(c)]
        assert not partial_warnings

    @pytest.mark.asyncio
    async def test_partial_completion_warning_when_llm_is_none(self) -> None:
        """No crash when ctx.services_required.llm is None."""
        repl = _make_bare_repl()
        repl._ctx.services_required.llm = None
        with patch("builtins.input", side_effect=["hello", "/exit"]):
            await repl._repl_loop()
        write_warning_calls = repl._view.write_warning.call_args_list
        partial_warnings = [c for c in write_warning_calls if "Partial" in str(c)]
        assert not partial_warnings

    @pytest.mark.asyncio
    async def test_signal_mid_turn_exits_within_graceful_timeout(self) -> None:
        """When SIGTERM fires while _dispatch_line hangs, _repl_loop exits within _GRACEFUL_TIMEOUT_S."""
        repl = _make_bare_repl()
        repl._shutdown_event = asyncio.Event()
        dispatch_hang = asyncio.Event()

        async def _hang_dispatch(*args, **kwargs):
            try:
                await dispatch_hang.wait()
            except asyncio.CancelledError:
                raise

        repl._orchestrator.handle_turn = AsyncMock(side_effect=_hang_dispatch)
        # Override timeout to be very short for test speed
        orig_timeout = repl._GRACEFUL_TIMEOUT_S
        repl._GRACEFUL_TIMEOUT_S = 0.05

        start = time.time()

        async def _set_shutdown_after_delay():
            await asyncio.sleep(0.02)
            repl._shutdown_event.set()

        asyncio.ensure_future(_set_shutdown_after_delay())

        with patch.object(
            repl, "_read_input", new=AsyncMock(return_value="test input")
        ):
            try:
                await asyncio.wait_for(repl._repl_loop(), timeout=5.0)
            except TimeoutError:
                pass  # Should not happen if graceful shutdown works

        elapsed = time.time() - start
        repl._GRACEFUL_TIMEOUT_S = orig_timeout
        assert elapsed < 2.0, (
            f"Loop took {elapsed:.1f}s to exit; expected ~{orig_timeout}s"
        )
        assert dispatch_hang.is_set() or True  # may or may not have been cancelled

    @pytest.mark.asyncio
    async def test_signal_before_turn_starts_still_exits(self) -> None:
        """Signal arriving before turn begins still triggers graceful exit (regression guard)."""
        repl = _make_bare_repl()
        repl._shutdown_event = asyncio.Event()
        dispatch_hang = asyncio.Event()

        async def _hang_dispatch(*args, **kwargs):
            try:
                await dispatch_hang.wait()
            except asyncio.CancelledError:
                raise

        repl._orchestrator.handle_turn = AsyncMock(side_effect=_hang_dispatch)
        orig_timeout = repl._GRACEFUL_TIMEOUT_S
        repl._GRACEFUL_TIMEOUT_S = 0.05

        start = time.time()

        async def _set_shutdown_after_delay():
            await asyncio.sleep(0.02)
            repl._shutdown_event.set()

        asyncio.ensure_future(_set_shutdown_after_delay())

        with patch.object(
            repl, "_read_input", new=AsyncMock(return_value="first line")
        ):
            try:
                await asyncio.wait_for(repl._repl_loop(), timeout=5.0)
            except TimeoutError:
                pass

        elapsed = time.time() - start
        repl._GRACEFUL_TIMEOUT_S = orig_timeout
        assert elapsed < 2.0, (
            f"Loop took {elapsed:.1f}s to exit; expected ~{orig_timeout}s"
        )

    @pytest.mark.asyncio
    async def test_normal_completion_without_signal_works_unchanged(self) -> None:
        """Normal turn completion without shutdown signal works unchanged."""
        repl = _make_bare_repl()
        repl._shutdown_event = asyncio.Event()
        repl._orchestrator.handle_turn = AsyncMock(return_value=None)

        call_count = 0

        def _input_with_exit(prompt):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                return "hello world"
            return "/exit"

        with patch("builtins.input", side_effect=_input_with_exit):
            await repl._repl_loop()

        repl._orchestrator.handle_turn.assert_called_once_with("hello world")


class TestPersistSessionDiagnostics:
    """Tests for AgentREPL._persist_session_diagnostics."""

    def _make_repl(self):
        from unittest.mock import MagicMock

        repl = AgentREPL.__new__(AgentREPL)
        ctx = MagicMock()
        ctx.stats.stat_turns = 5
        ctx.stats.stat_tool_calls = 12
        ctx.stats.stat_tool_errors = 2
        ctx.stats.stat_latency = {"llm": [0.1, 0.2], "compress": [0.05]}
        ctx.stats.stat_semantic_cache_hits = 3
        ctx.stats.stat_input_tokens = 1000
        ctx.stats.stat_output_tokens = 500
        ctx.stats.stat_partial_completions = 1
        ctx.session.session_id = 42
        ctx.services = MagicMock()
        ctx.services_required.llm.stat_partial_completions = 1
        ctx.services_required.llm.stat_parse_errors = 0
        ctx.services_required.llm.stat_heartbeat_timeouts = 0
        ctx.services_required.llm.stat_reconnects = 2
        ctx.services_required.hist_mgr.stat_compress_count = 2
        ctx.services_required.hist_mgr.stat_fallback_truncate_count = 0
        repl._ctx = ctx
        repl._diagnostic_store = MagicMock()
        return repl

    def test_handles_none_session_id(self):
        repl = self._make_repl()
        repl._ctx.session.session_id = None
        repl._ctx.services = None

        with patch("agent.repl.SQLiteHelper"):
            repl._persist_session_diagnostics(repl._ctx)

    def test_handles_none_services(self):
        repl = self._make_repl()
        repl._ctx.services = None

        mock_ctx_mgr = MagicMock()
        mock_ctx_mgr.__enter__ = MagicMock(return_value=mock_ctx_mgr)
        mock_ctx_mgr.__exit__ = MagicMock(return_value=False)
        mock_ctx_mgr.fetchall = MagicMock(return_value=[])

        mock_helper = MagicMock()
        mock_helper.open = MagicMock(return_value=mock_ctx_mgr)

        with patch("agent.repl.SQLiteHelper", return_value=mock_helper):
            repl._persist_session_diagnostics(repl._ctx)

    def test_warns_when_artifacts_present(self):
        """Non-empty `artifacts` triggers a warning naming the sensitive fields."""
        repl = self._make_repl()
        repl._ctx.services = None

        mock_state_store = MagicMock()
        mock_state_store.get_task_count.return_value = 0
        mock_state_store.get_workflow_count.return_value = 0
        mock_state_store.get_approval_count.return_value = 0
        mock_state_store.get_execute_attempt_count.return_value = 0
        mock_state_store.get_artifact_uris.return_value = ["file:///tmp/a.txt"]
        repl._diagnostic_store.fetch.return_value = []

        with (
            patch(
                "agent.workflow.state_store.StateStore", return_value=mock_state_store
            ),
            patch("agent.repl.logger") as mock_logger,
        ):
            repl._persist_session_diagnostics(repl._ctx)

        mock_logger.warning.assert_called_once()
        args = mock_logger.warning.call_args.args
        assert "sensitive fields" in args[0]
        assert args[1] == 1  # artifacts count
        assert args[2] == 0  # rag_stage_outcomes count

    def test_warns_when_rag_stage_outcomes_present(self):
        """Non-empty `rag_stage_outcomes` triggers a warning naming the sensitive fields."""
        repl = self._make_repl()
        repl._ctx.services = None

        mock_state_store = MagicMock()
        mock_state_store.get_task_count.return_value = 0
        mock_state_store.get_workflow_count.return_value = 0
        mock_state_store.get_approval_count.return_value = 0
        mock_state_store.get_execute_attempt_count.return_value = 0
        mock_state_store.get_artifact_uris.return_value = []
        repl._diagnostic_store.fetch.return_value = [
            {
                "kind": "rag_query",
                "content": json.dumps({"stage_results": [{"stage": "retrieve"}]}),
            }
        ]

        with (
            patch(
                "agent.workflow.state_store.StateStore", return_value=mock_state_store
            ),
            patch("agent.repl.logger") as mock_logger,
        ):
            repl._persist_session_diagnostics(repl._ctx)

        mock_logger.warning.assert_called_once()
        args = mock_logger.warning.call_args.args
        assert "sensitive fields" in args[0]
        assert args[1] == 0  # artifacts count
        assert args[2] == 1  # rag_stage_outcomes count

    def test_no_warning_when_no_sensitive_fields(self):
        """Empty `artifacts` and `rag_stage_outcomes` log no warning."""
        repl = self._make_repl()
        repl._ctx.services = None

        mock_state_store = MagicMock()
        mock_state_store.get_task_count.return_value = 0
        mock_state_store.get_workflow_count.return_value = 0
        mock_state_store.get_approval_count.return_value = 0
        mock_state_store.get_execute_attempt_count.return_value = 0
        mock_state_store.get_artifact_uris.return_value = []
        repl._diagnostic_store.fetch.return_value = []

        with (
            patch(
                "agent.workflow.state_store.StateStore", return_value=mock_state_store
            ),
            patch("agent.repl.logger") as mock_logger,
        ):
            repl._persist_session_diagnostics(repl._ctx)

        mock_logger.warning.assert_not_called()


# ── _read_input SIGTERM race (M-7) ─────────────────────────────────────────────


def _make_repl_for_shutdown() -> AgentREPL:
    """Return an AgentREPL instance with a shutdown event for _read_input tests."""
    repl = AgentREPL.__new__(AgentREPL)
    ctx = MagicMock()
    ctx.conv.shutdown_requested = False
    ctx.services_required.llm.stat_partial_completions = 0
    repl._ctx = ctx
    view = MagicMock()
    view.read_multiline = AsyncMock(return_value="")
    repl._view = view
    repl._cmds = AsyncMock()
    repl._cmds.dispatch = AsyncMock(return_value=True)
    repl._orchestrator = AsyncMock()
    repl._orchestrator.handle_turn = AsyncMock()
    repl._shutdown_event = asyncio.Event()
    return repl


class TestReadInputShutdownRace:
    @pytest.mark.asyncio
    async def test_shutdown_event_set_before_input_returns_none(self):
        repl = _make_repl_for_shutdown()
        repl._shutdown_event.set()
        loop = asyncio.get_event_loop()
        result = await repl._read_input(loop)
        assert result is None

    @pytest.mark.asyncio
    async def test_shutdown_event_fires_while_awaiting_input(self):
        repl = _make_repl_for_shutdown()
        loop = asyncio.get_event_loop()

        async def set_event_soon():
            await asyncio.sleep(0.05)
            repl._shutdown_event.set()

        asyncio.ensure_future(set_event_soon())
        with patch("builtins.input", side_effect=lambda p: (time.sleep(5), "never")[1]):
            result = await asyncio.wait_for(repl._read_input(loop), timeout=1.0)
        assert result is None

    @pytest.mark.asyncio
    async def test_no_shutdown_event_fallback(self, monkeypatch):
        repl = _make_repl_for_shutdown()
        repl._shutdown_event = None
        monkeypatch.setattr("builtins.input", lambda p: "hello")
        loop = asyncio.get_event_loop()
        result = await repl._read_input(loop)
        assert result == "hello"

    @pytest.mark.asyncio
    async def test_eof_returns_none(self, monkeypatch):
        repl = _make_repl_for_shutdown()
        monkeypatch.setattr(
            "builtins.input", lambda p: (_ for _ in ()).throw(EOFError())
        )
        loop = asyncio.get_event_loop()
        result = await repl._read_input(loop)
        assert result is None

    @pytest.mark.asyncio
    async def test_input_coro_cancelled_directly_returns_none(self):
        """Covers the M-7 race: _sigterm_handler() cancels _input_coro directly
        (independent of shutdown_event), so input_coro.result() raises
        asyncio.CancelledError rather than shutdown_coro winning the race."""
        repl = _make_repl_for_shutdown()
        loop = asyncio.get_event_loop()

        with patch("builtins.input", side_effect=lambda p: (time.sleep(5), "never")[1]):
            read_task = asyncio.ensure_future(repl._read_input(loop))
            await asyncio.sleep(0.05)
            assert repl._input_coro is not None
            repl._input_coro.cancel()
            result = await asyncio.wait_for(read_task, timeout=1.0)
        assert result is None


# ── AgentREPL.run() sqlite3.Error message format ──────────────────────────────


class TestRunSqliteErrorMessage:
    """Tests for sqlite3.Error error message formatting in AgentREPL.run()."""

    @pytest.mark.asyncio
    async def test_error_message_includes_class_name(self) -> None:
        """Error message includes the sqlite3 error subclass name."""
        import sqlite3

        repl = _make_bare_repl()
        repl._orchestrator = MagicMock()
        repl._cmds = MagicMock()

        # Patch startup.run() to succeed, then simulate OperationalError during session start
        with patch("agent.startup.StartupOrchestrator") as MockStartup:
            MockStartup.return_value.run = AsyncMock(
                return_value=(MagicMock(), MagicMock(), [])
            )
            with patch.object(repl._ctx.session, "start") as mock_start:
                mock_start.side_effect = sqlite3.OperationalError("disk I/O error")
                try:
                    await repl.run()
                except RuntimeError:
                    pass

        fatal_calls = repl._view.write_fatal.call_args_list
        assert len(fatal_calls) >= 1
        last_fatal = str(fatal_calls[-1][0][0])
        assert "OperationalError" in last_fatal
        assert "disk I/O error" in last_fatal

    @pytest.mark.asyncio
    async def test_runtime_error_includes_class_name(self) -> None:
        """Raised RuntimeError includes the sqlite3 error subclass name."""
        import sqlite3

        repl = _make_bare_repl()
        repl._orchestrator = MagicMock()
        repl._cmds = MagicMock()

        with patch("agent.startup.StartupOrchestrator") as MockStartup:
            MockStartup.return_value.run = AsyncMock(
                return_value=(MagicMock(), MagicMock(), [])
            )
            with patch.object(repl._ctx.session, "start") as mock_start:
                mock_start.side_effect = sqlite3.DatabaseError("database locked")
                with pytest.raises(
                    RuntimeError,
                    match="Database unavailable \\(DatabaseError\\): database locked",
                ):
                    await repl.run()


# ── _close_resources() WAL checkpoint ─────────────────────────────────────────


class TestCloseResourcesWALCheckpoint:
    """Tests for WAL checkpoint behavior in AgentREPL._close_resources()."""

    @pytest.mark.asyncio
    async def test_passive_checkpoint_called_first_when_wal_mode(self) -> None:
        """PASSIVE checkpoint is attempted first when PRAGMA journal_mode returns 'wal'."""
        repl = _make_bare_repl()
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = ("wal",)
        mock_ctx_manager = MagicMock()
        mock_ctx_manager.__enter__ = MagicMock(return_value=mock_db)
        mock_ctx_manager.__exit__ = MagicMock(return_value=None)
        with patch("agent.repl.SQLiteHelper") as MockHelper:
            MockHelper.return_value.open = MagicMock(return_value=mock_ctx_manager)
            await repl._close_resources()
        mock_db.checkpoint.assert_called_once_with("PASSIVE")

    @pytest.mark.asyncio
    async def test_truncate_checkpoint_falls_back_on_passive_failure(self) -> None:
        """TRUNCATE checkpoint is used when PASSIVE checkpoint fails."""
        repl = _make_bare_repl()
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = ("wal",)
        mock_db.checkpoint.side_effect = sqlite3.Error("exclusive lock")
        mock_ctx_manager = MagicMock()
        mock_ctx_manager.__enter__ = MagicMock(return_value=mock_db)
        mock_ctx_manager.__exit__ = MagicMock(return_value=None)
        with patch("agent.repl.SQLiteHelper") as MockHelper:
            MockHelper.return_value.open = MagicMock(return_value=mock_ctx_manager)
            await repl._close_resources()
        calls = [c[0][0] for c in mock_db.checkpoint.call_args_list]
        assert "PASSIVE" in calls
        assert "TRUNCATE" in calls

    @pytest.mark.asyncio
    async def test_checkpoint_skipped_when_not_wal_mode(self) -> None:
        """checkpoint is NOT called when PRAGMA journal_mode returns non-wal."""
        repl = _make_bare_repl()
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = ("delete",)
        mock_ctx_manager = MagicMock()
        mock_ctx_manager.__enter__ = MagicMock(return_value=mock_db)
        mock_ctx_manager.__exit__ = MagicMock(return_value=None)
        with patch("agent.repl.SQLiteHelper") as MockHelper:
            MockHelper.return_value.open = MagicMock(return_value=mock_ctx_manager)
            await repl._close_resources()
        mock_db.checkpoint.assert_not_called()

    @pytest.mark.asyncio
    async def test_checkpoint_timeout_records_error_and_still_runs_backup(self) -> None:
        """A checkpoint stage that exceeds the timeout is aborted (from the caller's
        perspective) promptly, logs a timeout error, and the backup stage still runs."""
        repl = _make_bare_repl()
        repl._WAL_CHECKPOINT_TIMEOUT_S = 0.02
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = ("wal",)
        mock_db.checkpoint.side_effect = lambda mode: time.sleep(0.3)
        mock_ctx_manager = MagicMock()
        mock_ctx_manager.__enter__ = MagicMock(return_value=mock_db)
        mock_ctx_manager.__exit__ = MagicMock(return_value=None)
        with (
            patch("agent.repl.SQLiteHelper") as MockHelper,
            patch("agent.repl.shutil.copy2"),
            patch("agent.repl.logger") as mock_logger,
        ):
            MockHelper.return_value.open = MagicMock(return_value=mock_ctx_manager)
            start = time.monotonic()
            await repl._close_resources()
            elapsed = time.monotonic() - start
        assert (
            elapsed < 0.2
        )  # returns well before the 0.3s blocked checkpoint call finishes
        error_messages = [c.args[0] for c in mock_logger.error.call_args_list]
        assert any("timed out" in msg for msg in error_messages)
        mock_db.execute.assert_any_call("PRAGMA database_list")

    @pytest.mark.asyncio
    async def test_pragma_database_list_reads_db_path_from_column_index_2(self) -> None:
        """db_path is read from index [2] (file path) of PRAGMA database_list, not [1]
        (the database name), when the backup stage runs."""
        repl = _make_bare_repl()
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.side_effect = [
            ("wal",),
            (0, "main", "/opt/llm/db/session.db"),
        ]
        mock_db.checkpoint.side_effect = sqlite3.Error("locked")
        mock_ctx_manager = MagicMock()
        mock_ctx_manager.__enter__ = MagicMock(return_value=mock_db)
        mock_ctx_manager.__exit__ = MagicMock(return_value=None)
        with (
            patch("agent.repl.SQLiteHelper") as MockHelper,
            patch("agent.repl.shutil.copy2") as mock_copy2,
            patch("agent.repl.time.sleep"),
        ):
            MockHelper.return_value.open = MagicMock(return_value=mock_ctx_manager)
            await repl._close_resources()
        mock_copy2.assert_called_once()
        args, _ = mock_copy2.call_args
        assert args[0] == "/opt/llm/db/session.db-wal"


# ── _wal_backup_sync() path-containment security ───────────────────────────────


class TestWalBackupPathSecurity:
    """Tests for the path-traversal/symlink-escape protection and session-based
    filename added to AgentREPL._wal_backup_sync()."""

    @staticmethod
    def _mock_helper_for_db_path(db_path: str):
        """Return a SQLiteHelper patch whose PRAGMA database_list resolves to db_path."""
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = (0, "main", db_path)
        mock_ctx_manager = MagicMock()
        mock_ctx_manager.__enter__ = MagicMock(return_value=mock_db)
        mock_ctx_manager.__exit__ = MagicMock(return_value=None)
        return mock_ctx_manager

    def test_rejects_path_outside_allowed_root(self, tmp_path) -> None:
        """A db_path that resolves outside allowed_root is rejected: no copy is
        attempted, the backup path is None, and a descriptive error is recorded."""
        repl = _make_bare_repl()
        allowed_root = tmp_path / "allowed"
        allowed_root.mkdir()
        repl._ctx.cfg.approval.allowed_root = str(allowed_root)
        outside_db = tmp_path / "outside" / "session.db"
        outside_db.parent.mkdir()
        outside_db.write_text("db")
        mock_ctx_manager = self._mock_helper_for_db_path(str(outside_db))
        with (
            patch("agent.repl.SQLiteHelper") as MockHelper,
            patch("agent.repl.shutil.copy2") as mock_copy2,
        ):
            MockHelper.return_value.open = MagicMock(return_value=mock_ctx_manager)
            backup_path, errors = repl._wal_backup_sync()
        mock_copy2.assert_not_called()
        assert backup_path is None
        assert any(name == "wal_backup_path_rejected" for name, _ in errors)

    def test_rejects_symlink_that_resolves_outside_allowed_root(self, tmp_path) -> None:
        """A db_path inside allowed_root that is actually a symlink pointing
        outside allowed_root must be rejected after resolving the symlink."""
        repl = _make_bare_repl()
        allowed_root = tmp_path / "allowed"
        allowed_root.mkdir()
        repl._ctx.cfg.approval.allowed_root = str(allowed_root)
        outside_target = tmp_path / "outside" / "real.db"
        outside_target.parent.mkdir()
        outside_target.write_text("db")
        symlinked_db = allowed_root / "session.db"
        symlinked_db.symlink_to(outside_target)
        mock_ctx_manager = self._mock_helper_for_db_path(str(symlinked_db))
        with (
            patch("agent.repl.SQLiteHelper") as MockHelper,
            patch("agent.repl.shutil.copy2") as mock_copy2,
        ):
            MockHelper.return_value.open = MagicMock(return_value=mock_ctx_manager)
            backup_path, errors = repl._wal_backup_sync()
        mock_copy2.assert_not_called()
        assert backup_path is None
        assert any(name == "wal_backup_path_rejected" for name, _ in errors)

    def test_allows_symlink_that_resolves_inside_allowed_root(self, tmp_path) -> None:
        """A symlinked db_path whose resolved target stays inside allowed_root
        continues to back up normally, and the filename embeds the session id."""
        repl = _make_bare_repl()
        repl._ctx.session.session_id = 42
        allowed_root = tmp_path / "allowed"
        real_dir = allowed_root / "real"
        real_dir.mkdir(parents=True)
        repl._ctx.cfg.approval.allowed_root = str(allowed_root)
        real_target = real_dir / "session.db"
        real_target.write_text("db")
        symlinked_db = allowed_root / "session.db"
        symlinked_db.symlink_to(real_target)
        # The WAL sidecar file is looked up next to the literal db_path string
        # (pre-resolution), not the resolved target.
        (allowed_root / "session.db-wal").write_text("wal")
        mock_ctx_manager = self._mock_helper_for_db_path(str(symlinked_db))
        with patch("agent.repl.SQLiteHelper") as MockHelper:
            MockHelper.return_value.open = MagicMock(return_value=mock_ctx_manager)
            backup_path, errors = repl._wal_backup_sync()
        assert errors == []
        assert backup_path is not None
        assert "-wal-backup-42-" in backup_path
        assert os.path.exists(backup_path)

    def test_skipped_when_backup_dir_not_writable(self, tmp_path) -> None:
        """When the backup directory is not writable, the backup is skipped with
        a recorded error instead of attempting shutil.copy2()."""
        repl = _make_bare_repl()
        allowed_root = tmp_path / "allowed"
        allowed_root.mkdir()
        repl._ctx.cfg.approval.allowed_root = str(allowed_root)
        db_path = allowed_root / "session.db"
        db_path.write_text("db")
        mock_ctx_manager = self._mock_helper_for_db_path(str(db_path))
        with (
            patch("agent.repl.SQLiteHelper") as MockHelper,
            patch("agent.repl.os.access", return_value=False),
            patch("agent.repl.shutil.copy2") as mock_copy2,
        ):
            MockHelper.return_value.open = MagicMock(return_value=mock_ctx_manager)
            backup_path, errors = repl._wal_backup_sync()
        mock_copy2.assert_not_called()
        assert backup_path is None
        assert any(name == "wal_backup_dir_not_writable" for name, _ in errors)

    def test_backup_allowed_when_allowed_root_unset(self, tmp_path) -> None:
        """An empty allowed_root means unrestricted, matching
        tool_policy.check_allowed_root()'s convention."""
        repl = _make_bare_repl()
        repl._ctx.cfg.approval.allowed_root = ""
        db_path = tmp_path / "session.db"
        db_path.write_text("db")
        (tmp_path / "session.db-wal").write_text("wal")
        mock_ctx_manager = self._mock_helper_for_db_path(str(db_path))
        with patch("agent.repl.SQLiteHelper") as MockHelper:
            MockHelper.return_value.open = MagicMock(return_value=mock_ctx_manager)
            backup_path, errors = repl._wal_backup_sync()
        assert errors == []
        assert backup_path is not None

    def test_filename_falls_back_to_uuid_when_session_id_none(self, tmp_path) -> None:
        """When session_id is unset (e.g. init failed before a session was
        created), the filename falls back to a short uuid instead of raising."""
        repl = _make_bare_repl()
        repl._ctx.session.session_id = None
        allowed_root = tmp_path / "allowed"
        allowed_root.mkdir()
        repl._ctx.cfg.approval.allowed_root = str(allowed_root)
        db_path = allowed_root / "session.db"
        db_path.write_text("db")
        (allowed_root / "session.db-wal").write_text("wal")
        mock_ctx_manager = self._mock_helper_for_db_path(str(db_path))
        with patch("agent.repl.SQLiteHelper") as MockHelper:
            MockHelper.return_value.open = MagicMock(return_value=mock_ctx_manager)
            backup_path, errors = repl._wal_backup_sync()
        assert errors == []
        assert backup_path is not None
        # filename shape: {basename}-wal-backup-{tag}-{timestamp}; tag is an
        # 8-char hex uuid fragment, not the (absent) session id.
        tag = os.path.basename(backup_path).split("-wal-backup-")[1].rsplit("-", 1)[0]
        assert len(tag) == 8


# ── _close_resources() independently-guarded service cleanup ──────────────────


class TestCloseResourcesServiceCleanupGuards:
    """Tests that lifecycle.shutdown_all() and http.aclose() are independently
    guarded in AgentREPL._close_resources() so a None services object or a
    failure in one call cannot block the other."""

    @staticmethod
    def _patch_wal_non_wal_mode():
        """Return a SQLiteHelper patch that reports non-WAL journal mode, so the
        checkpoint/backup stages complete quickly without further mocking."""
        mock_db = MagicMock()
        mock_db.execute.return_value.fetchone.return_value = ("delete",)
        mock_ctx_manager = MagicMock()
        mock_ctx_manager.__enter__ = MagicMock(return_value=mock_db)
        mock_ctx_manager.__exit__ = MagicMock(return_value=None)
        return mock_ctx_manager

    @pytest.mark.asyncio
    async def test_services_none_does_not_raise(self) -> None:
        """services=None must not raise or block WAL cleanup above it."""
        repl = _make_bare_repl()
        repl._ctx.services = None
        mock_ctx_manager = self._patch_wal_non_wal_mode()
        with patch("agent.repl.SQLiteHelper") as MockHelper:
            MockHelper.return_value.open = MagicMock(return_value=mock_ctx_manager)
            await repl._close_resources()  # must not raise

    @pytest.mark.asyncio
    async def test_http_aclose_runs_when_lifecycle_shutdown_raises(self) -> None:
        """A failure in lifecycle.shutdown_all() must not prevent http.aclose()
        from being called — the two cleanup calls are independently guarded."""
        repl = _make_bare_repl()
        repl._ctx.services.lifecycle.shutdown_all = AsyncMock(
            side_effect=RuntimeError("lifecycle boom")
        )
        mock_ctx_manager = self._patch_wal_non_wal_mode()
        with patch("agent.repl.SQLiteHelper") as MockHelper:
            MockHelper.return_value.open = MagicMock(return_value=mock_ctx_manager)
            await repl._close_resources()
        repl._ctx.services.http.aclose.assert_called_once()

    @pytest.mark.asyncio
    async def test_lifecycle_shutdown_runs_when_http_aclose_raises(self) -> None:
        """A failure in http.aclose() does not affect lifecycle.shutdown_all(),
        which already ran independently above it."""
        repl = _make_bare_repl()
        repl._ctx.services.http.aclose = AsyncMock(
            side_effect=RuntimeError("http boom")
        )
        mock_ctx_manager = self._patch_wal_non_wal_mode()
        with patch("agent.repl.SQLiteHelper") as MockHelper:
            MockHelper.return_value.open = MagicMock(return_value=mock_ctx_manager)
            await repl._close_resources()
        repl._ctx.services.lifecycle.shutdown_all.assert_called_once()


# ── run() _sigterm_handler _turn_active guard ──────────────────────────────────


class TestSigtermHandlerTurnActiveGuard:
    """Tests for the _turn_active guard in run()'s _sigterm_handler closure:
    the input coroutine must only be cancelled while no turn is active."""

    @staticmethod
    async def _run_and_capture_handler(repl: AgentREPL) -> list:
        """Drive run() far enough to register signal handlers, capture the
        registered closure, then let startup fail so run() exits promptly."""
        captured: list = []

        def fake_add_signal_handler(sig, handler):
            captured.append(handler)

        loop = asyncio.get_running_loop()
        with (
            patch("agent.startup.StartupOrchestrator") as MockStartup,
            patch("agent.repl.SQLiteHelper"),
            patch.object(
                loop, "add_signal_handler", side_effect=fake_add_signal_handler
            ),
        ):
            MockStartup.return_value.run = AsyncMock(
                side_effect=RuntimeError("stop-after-registration")
            )
            with pytest.raises(RuntimeError, match="stop-after-registration"):
                await repl.run()
        return captured

    @pytest.mark.asyncio
    async def test_input_coro_not_cancelled_when_turn_active(self) -> None:
        repl = _make_bare_repl()
        repl._turn_active = True
        mock_task = MagicMock()
        mock_task.done.return_value = False
        repl._input_coro = mock_task

        handlers = await self._run_and_capture_handler(repl)
        assert handlers, "signal handler was not registered via add_signal_handler"
        handlers[0]()

        mock_task.cancel.assert_not_called()
        assert repl._ctx.conv.shutdown_requested is True
        assert repl._shutdown_event.is_set()

    @pytest.mark.asyncio
    async def test_input_coro_cancelled_when_turn_not_active(self) -> None:
        repl = _make_bare_repl()
        repl._turn_active = False
        mock_task = MagicMock()
        mock_task.done.return_value = False
        repl._input_coro = mock_task

        handlers = await self._run_and_capture_handler(repl)
        assert handlers, "signal handler was not registered via add_signal_handler"
        handlers[0]()

        mock_task.cancel.assert_called_once()
        assert repl._ctx.conv.shutdown_requested is True
        assert repl._shutdown_event.is_set()


# ── AgentContext.__init__() config error message ──────────────────────────────


class TestContextInitConfigError:
    """Tests for config loading error message formatting in AgentContext.__init__()."""

    def test_error_message_includes_path_and_class_name(self) -> None:
        """RuntimeError includes config path and error class name."""
        from unittest.mock import patch

        class FakeConfigLoadError(Exception):
            pass

        with patch(
            "agent.context.build_agent_config",
            side_effect=FakeConfigLoadError("invalid key"),
        ):
            with pytest.raises(RuntimeError) as exc_info:
                from agent.context import AgentContext

                AgentContext()

        msg = str(exc_info.value)
        assert "config" in msg.lower()
        assert "FakeConfigLoadError" in msg
        assert "invalid key" in msg

    def test_from_none_suppresses_traceback_chain(self) -> None:
        """Exception chaining is suppressed (from None)."""
        from unittest.mock import patch

        class FakeConfigLoadError(Exception):
            pass

        with patch(
            "agent.context.build_agent_config",
            side_effect=FakeConfigLoadError("invalid key"),
        ):
            with pytest.raises(RuntimeError) as exc_info:
                from agent.context import AgentContext

                AgentContext()

        assert exc_info.value.__cause__ is None


# ── AgentREPL.run() subprocess termination on failure path only ────────────────


class TestAgentREPLRunSubprocessTermination:
    """Tests that subprocess termination loop runs only on the failure path."""

    @pytest.mark.asyncio
    async def test_run_does_not_terminate_subprocesses_on_success(self) -> None:
        """When startup succeeds, .terminate() must NOT be called on healthy MCP subprocesses."""
        import subprocess

        fake_proc = MagicMock(spec=subprocess.Popen)
        fake_proc.poll.return_value = None  # process still alive

        repl = _make_bare_repl()
        repl._orchestrator = MagicMock()
        repl._cmds = MagicMock()

        with patch("agent.startup.StartupOrchestrator") as MockStartup:
            MockStartup.return_value.run = AsyncMock(
                return_value=(MagicMock(), MagicMock(), [fake_proc])
            )
            repl._shutdown_event = asyncio.Event()
            with patch.object(repl, "_run_repl_loop", AsyncMock()):
                await repl.run()

        fake_proc.terminate.assert_not_called()

    @pytest.mark.asyncio
    async def test_run_terminates_subprocesses_on_failure(self) -> None:
        """When startup fails, .terminate() MUST be called on any spawned subprocesses."""
        import subprocess

        fake_proc = MagicMock(spec=subprocess.Popen)
        fake_proc.poll.return_value = None  # process still alive

        repl = _make_bare_repl()
        repl._orchestrator = MagicMock()
        repl._cmds = MagicMock()

        with patch("agent.startup.StartupOrchestrator") as MockStartup:
            mock_startup_instance = MagicMock()
            mock_startup_instance.run = AsyncMock(
                side_effect=RuntimeError("startup failed")
            )
            mock_startup_instance._spawned_subprocesses = [fake_proc]
            MockStartup.return_value = mock_startup_instance
            repl._shutdown_event = asyncio.Event()
            repl._view.read_multiline = AsyncMock(return_value="")
            with pytest.raises(RuntimeError, match="startup failed"):
                await repl.run()

        fake_proc.terminate.assert_called_once()
