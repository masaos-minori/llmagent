"""tests/test_repl.py
Behavior-lock tests for agent/repl.py: AgentREPL._repl_loop and _get_chunk_count.

MCP server startup tests (formerly TestStartSubprocessServers) were moved to
tests/test_startup.py when _start_subprocess_servers was extracted to
StartupOrchestrator._start_servers().
"""

from __future__ import annotations

import asyncio
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


# ── _start_subprocess_servers ─────────────────────────────────────────────────


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
