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
        repl._ctx = ctx
        repl._diagnostic_store = MagicMock()
        return repl

    def test_writes_jsonl_file(self, tmp_path):
        import json as json_mod

        repl = self._make_repl()
        diag_file = tmp_path / "diagnostics.jsonl"
        parent_dir = diag_file.parent

        mock_row = {"cnt": 8, "errs": 3}
        mock_helper = MagicMock()
        mock_ctx_mgr = MagicMock()
        mock_ctx_mgr.__enter__ = MagicMock(return_value=mock_helper)
        mock_ctx_mgr.__exit__ = MagicMock(return_value=False)
        mock_helper.open = MagicMock(return_value=mock_ctx_mgr)
        mock_helper.fetchall = MagicMock(return_value=[mock_row])

        with (
            patch("agent.repl.build_db_config") as mock_cfg,
            patch("agent.repl.SQLiteHelper", return_value=mock_helper),
        ):
            mock_cfg.return_value.session_db_path = str(parent_dir / "session.sqlite")
            repl._persist_session_diagnostics(repl._ctx)

        assert diag_file.exists()
        lines = diag_file.read_text().strip().split("\n")
        assert len(lines) == 1
        data = json_mod.loads(lines[0])
        assert data["session_id"] == 42
        assert data["turns"] == 5
        assert data["tool_calls"] == 12
        assert data["tool_errors"] == 2
        assert data["partial_completions"] == 1
        assert data["reconnects"] == 2
        assert data["semantic_cache_hits"] == 3
        assert data["input_tokens"] == 1000
        assert data["output_tokens"] == 500
        assert data["compress_count"] == 2
        assert "llm" in data["latency_summary"]
        assert data["latency_summary"]["llm"]["count"] == 2
        assert data["tool_result_summary"]["total"] == 8
        assert data["tool_result_summary"]["errors"] == 3

    def test_handles_none_session_id(self, tmp_path):
        repl = self._make_repl()
        repl._ctx.session.session_id = None

        mock_helper = MagicMock()
        mock_ctx_mgr = MagicMock()
        mock_ctx_mgr.__enter__ = MagicMock(return_value=mock_helper)
        mock_ctx_mgr.__exit__ = MagicMock(return_value=False)

        with (
            patch("agent.repl.build_db_config") as mock_cfg,
            patch("agent.repl.SQLiteHelper", return_value=mock_helper),
        ):
            mock_cfg.return_value.session_db_path = str(tmp_path / "session.sqlite")
            repl._persist_session_diagnostics(repl._ctx)

    def test_handles_none_services(self, tmp_path):
        repl = self._make_repl()
        repl._ctx.services = None

        mock_ctx_mgr = MagicMock()
        mock_ctx_mgr.__enter__ = MagicMock(return_value=mock_ctx_mgr)
        mock_ctx_mgr.__exit__ = MagicMock(return_value=False)
        mock_ctx_mgr.fetchall = MagicMock(return_value=[])

        mock_helper = MagicMock()
        mock_helper.open = MagicMock(return_value=mock_ctx_mgr)

        with (
            patch("agent.repl.build_db_config") as mock_cfg,
            patch("agent.repl.SQLiteHelper", return_value=mock_helper),
        ):
            mock_cfg.return_value.session_db_path = str(tmp_path / "session.sqlite")
            repl._persist_session_diagnostics(repl._ctx)
