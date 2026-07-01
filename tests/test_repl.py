"""tests/test_repl.py
Behavior-lock tests for agent/repl.py: AgentREPL._repl_loop and _get_chunk_count.

MCP server startup tests (formerly TestStartSubprocessServers) were moved to
tests/test_startup.py when _start_subprocess_servers was extracted to
StartupOrchestrator._start_servers().
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.repl import AgentREPL

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_bare_repl() -> AgentREPL:
    """Return an AgentREPL instance bypassing __init__ to avoid real deps."""
    repl = AgentREPL.__new__(AgentREPL)
    ctx = MagicMock()
    ctx.conv.shutdown_requested = False
    ctx.services.llm.stat_partial_completions = 0
    repl._ctx = ctx
    view = MagicMock()
    view.read_multiline = AsyncMock(return_value="")
    repl._view = view
    repl._cmds = AsyncMock()
    repl._cmds.dispatch = AsyncMock(return_value=True)
    repl._orchestrator = AsyncMock()
    repl._orchestrator.handle_turn = AsyncMock()
    return repl


# ── _get_chunk_count ──────────────────────────────────────────────────────────


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
        with patch("agent.repl.SQLiteHelper") as mock_helper:
            mock_helper.return_value.open.side_effect = RuntimeError("db gone")
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
        repl._ctx.services.llm.stat_partial_completions = 0

        def _increment_partial(*_args, **_kwargs):
            repl._ctx.services.llm.stat_partial_completions += 1

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
        repl._ctx.services.llm.stat_partial_completions = 0
        with patch("builtins.input", side_effect=["hello", "/exit"]):
            await repl._repl_loop()
        write_warning_calls = repl._view.write_warning.call_args_list
        partial_warnings = [c for c in write_warning_calls if "Partial" in str(c)]
        assert not partial_warnings

    @pytest.mark.asyncio
    async def test_partial_completion_warning_when_llm_is_none(self) -> None:
        """No crash when ctx.services.llm is None."""
        repl = _make_bare_repl()
        repl._ctx.services.llm = None
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
        ctx.session.session_id = 42
        ctx.services = MagicMock()
        ctx.services.llm.stat_partial_completions = 1
        ctx.services.llm.stat_parse_errors = 0
        ctx.services.llm.stat_heartbeat_timeouts = 0
        ctx.services.llm.stat_reconnects = 2
        ctx.services.hist_mgr.stat_compress_count = 2
        ctx.services.hist_mgr.stat_fallback_truncate_count = 0
        repl._ctx = ctx
        repl._diagnostic_store = MagicMock()
        return repl

    def test_handles_none_session_id(self):
        repl = self._make_repl()
        repl._ctx.session.session_id = None

        mock_helper = MagicMock()
        mock_ctx_mgr = MagicMock()
        mock_ctx_mgr.__enter__ = MagicMock(return_value=mock_helper)
        mock_ctx_mgr.__exit__ = MagicMock(return_value=False)
        mock_helper.fetchall = MagicMock(return_value=[])

        with patch("agent.repl.SQLiteHelper", return_value=mock_helper):
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
