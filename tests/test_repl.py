"""tests/test_repl.py
Behavior-lock tests for agent/repl.py: AgentREPL._repl_loop,
_start_subprocess_servers, and _get_chunk_count.

These tests are written BEFORE refactoring so that the refactor cannot
silently break observable behavior.
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.repl import AgentREPL
from shared.mcp_config import McpServerConfig

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


def _http_subprocess_cfg() -> McpServerConfig:
    return McpServerConfig(
        transport="http",
        url="http://127.0.0.1:9999",
        cmd=["uvicorn", "srv:app"],
        openrc_service="",
        startup_mode="subprocess",
    )


def _stdio_persistent_cfg() -> McpServerConfig:
    return McpServerConfig(
        transport="stdio",
        url="",
        cmd=["python", "server.py"],
        openrc_service="",
        startup_mode="persistent",
    )


def _stdio_ondemand_cfg() -> McpServerConfig:
    return McpServerConfig(
        transport="stdio",
        url="",
        cmd=["python", "server.py"],
        openrc_service="",
        startup_mode="ondemand",
    )


# ── _get_chunk_count ──────────────────────────────────────────────────────────


class TestGetChunkCount:
    def test_returns_formatted_count(self) -> None:
        repl = _make_bare_repl()
        mock_db = MagicMock()
        mock_db.fetchall.return_value = [(1234,)]
        mock_ctx_mgr = MagicMock()
        mock_ctx_mgr.__enter__ = MagicMock(return_value=mock_db)
        mock_ctx_mgr.__exit__ = MagicMock(return_value=False)

        with patch("agent.repl.SQLiteHelper") as mock_helper:
            mock_helper.return_value.open.return_value = mock_ctx_mgr
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
        mock_db = MagicMock()
        mock_db.fetchall.return_value = []
        mock_ctx_mgr = MagicMock()
        mock_ctx_mgr.__enter__ = MagicMock(return_value=mock_db)
        mock_ctx_mgr.__exit__ = MagicMock(return_value=False)

        with patch("agent.repl.SQLiteHelper") as mock_helper:
            mock_helper.return_value.open.return_value = mock_ctx_mgr
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
    async def test_unknown_slash_command_prints_hint(self, capsys) -> None:
        repl = _make_bare_repl()
        repl._cmds.dispatch = AsyncMock(return_value=False)
        with patch("builtins.input", side_effect=["/unknown_cmd", "/exit"]):
            await repl._repl_loop()
        captured = capsys.readouterr()
        assert "Unknown command" in captured.out
        assert "/unknown_cmd" in captured.out

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


class TestStartSubprocessServers:
    """Tests for MCP server startup dispatch."""

    def _make_repl_for_startup(
        self,
        mcp_servers: dict[str, McpServerConfig],
    ) -> AgentREPL:
        repl = _make_bare_repl()
        repl._ctx.cfg.mcp.mcp_servers = mcp_servers
        repl._ctx.services.tools = MagicMock()
        repl._ctx.services.tools.set_transport = MagicMock()
        repl._ctx.services.lifecycle = AsyncMock()
        repl._ctx.services.lifecycle.start_http_subprocess = AsyncMock()
        repl._ctx.services.stdio_procs = {}
        return repl

    @pytest.mark.asyncio
    async def test_http_subprocess_calls_lifecycle(self) -> None:
        cfg = _http_subprocess_cfg()
        repl = self._make_repl_for_startup({"web": cfg})

        await repl._start_subprocess_servers()

        repl._ctx.services.lifecycle.start_http_subprocess.assert_called_once_with(
            "web", cfg
        )

    @pytest.mark.asyncio
    async def test_http_subprocess_failure_is_swallowed(self) -> None:
        cfg = _http_subprocess_cfg()
        repl = self._make_repl_for_startup({"web": cfg})
        repl._ctx.services.lifecycle.start_http_subprocess.side_effect = RuntimeError(
            "port busy"
        )

        # Must not raise; failure is logged and printed
        await repl._start_subprocess_servers()

    @pytest.mark.asyncio
    async def test_persistent_stdio_registers_transport(self) -> None:
        cfg = _stdio_persistent_cfg()
        repl = self._make_repl_for_startup({"git": cfg})

        with patch("agent.repl.StdioTransport", autospec=True) as mock_transport_cls:
            mock_transport = AsyncMock()
            mock_transport.start = AsyncMock()
            mock_transport_cls.return_value = mock_transport

            await repl._start_subprocess_servers()

        mock_transport.start.assert_called_once()
        repl._ctx.services.tools.set_transport.assert_called_once_with(
            "git", mock_transport
        )
        assert repl._ctx.services.stdio_procs["git"] is mock_transport

    @pytest.mark.asyncio
    async def test_persistent_stdio_failure_is_swallowed(self) -> None:
        cfg = _stdio_persistent_cfg()
        repl = self._make_repl_for_startup({"git": cfg})

        with patch("agent.repl.StdioTransport", autospec=True) as mock_transport_cls:
            mock_transport = AsyncMock()
            mock_transport.start.side_effect = OSError("cannot start")
            mock_transport_cls.return_value = mock_transport

            # Must not raise
            await repl._start_subprocess_servers()

        repl._ctx.services.tools.set_transport.assert_not_called()

    @pytest.mark.asyncio
    async def test_ondemand_stdio_server_skipped(self) -> None:
        cfg = _stdio_ondemand_cfg()
        repl = self._make_repl_for_startup({"lazy": cfg})

        with patch("agent.repl.StdioTransport", autospec=True) as mock_transport_cls:
            await repl._start_subprocess_servers()

        mock_transport_cls.assert_not_called()
        repl._ctx.services.lifecycle.start_http_subprocess.assert_not_called()

    @pytest.mark.asyncio
    async def test_multiple_servers_all_processed(self) -> None:
        repl = self._make_repl_for_startup(
            {
                "http_srv": _http_subprocess_cfg(),
                "stdio_srv": _stdio_persistent_cfg(),
            }
        )

        with patch("agent.repl.StdioTransport", autospec=True) as mock_transport_cls:
            mock_transport = AsyncMock()
            mock_transport.start = AsyncMock()
            mock_transport_cls.return_value = mock_transport

            await repl._start_subprocess_servers()

        repl._ctx.services.lifecycle.start_http_subprocess.assert_called_once()
        mock_transport.start.assert_called_once()
