"""tests/test_startup.py
Behavior-lock tests for agent/startup.py: StartupOrchestrator._start_servers().

Migrated from TestStartSubprocessServers in tests/test_repl.py when
_start_subprocess_servers was moved to StartupOrchestrator._start_servers().
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.startup import StartupOrchestrator
from shared.mcp_config import McpServerConfig

# ── Helpers ───────────────────────────────────────────────────────────────────


def _make_startup(mcp_servers: dict[str, McpServerConfig]) -> StartupOrchestrator:
    """Return a StartupOrchestrator with mocked ctx/view for _start_servers() tests."""
    ctx = MagicMock()
    ctx.cfg.mcp.mcp_servers = mcp_servers
    ctx.services.tools = MagicMock()
    ctx.services.tools.set_transport = MagicMock()
    ctx.services.lifecycle = AsyncMock()
    ctx.services.lifecycle.start_http_subprocess = AsyncMock()
    ctx.services.stdio_procs = {}
    view = MagicMock()
    view.write_warning = MagicMock()
    return StartupOrchestrator(ctx, view)


def _http_subprocess_cfg() -> McpServerConfig:
    return McpServerConfig(
        transport="http",
        url="http://127.0.0.1:9999",
        cmd=["uvicorn", "srv:app"],
        startup_mode="subprocess",
    )


def _stdio_persistent_cfg() -> McpServerConfig:
    return McpServerConfig(
        transport="stdio",
        url="",
        cmd=["python", "server.py"],
        startup_mode="persistent",
    )


def _stdio_ondemand_cfg() -> McpServerConfig:
    return McpServerConfig(
        transport="stdio",
        url="",
        cmd=["python", "server.py"],
        startup_mode="ondemand",
    )


# ── StartupOrchestrator._start_servers ────────────────────────────────────────


class TestStartupOrchestratorStartServers:
    """Tests for StartupOrchestrator._start_servers()."""

    @pytest.mark.asyncio
    async def test_http_subprocess_calls_lifecycle(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg})

        await startup._start_servers()

        startup._ctx.services.lifecycle.start_http_subprocess.assert_called_once_with(
            "web", cfg
        )

    @pytest.mark.asyncio
    async def test_http_subprocess_failure_is_swallowed(self) -> None:
        cfg = _http_subprocess_cfg()
        startup = _make_startup({"web": cfg})
        startup._ctx.services.lifecycle.start_http_subprocess.side_effect = (
            RuntimeError("port busy")
        )

        # Must not raise; failure is logged and printed as warning
        await startup._start_servers()

    @pytest.mark.asyncio
    async def test_persistent_stdio_registers_transport(self) -> None:
        cfg = _stdio_persistent_cfg()
        startup = _make_startup({"git": cfg})

        with patch("agent.startup.StdioTransport", autospec=True) as mock_transport_cls:
            mock_transport = AsyncMock()
            mock_transport.start = AsyncMock()
            mock_transport_cls.return_value = mock_transport

            await startup._start_servers()

        mock_transport.start.assert_called_once()
        startup._ctx.services.tools.set_transport.assert_called_once_with(
            "git", mock_transport
        )
        assert startup._ctx.services.stdio_procs["git"] is mock_transport

    @pytest.mark.asyncio
    async def test_persistent_stdio_failure_is_swallowed(self) -> None:
        cfg = _stdio_persistent_cfg()
        startup = _make_startup({"git": cfg})

        with patch("agent.startup.StdioTransport", autospec=True) as mock_transport_cls:
            mock_transport = AsyncMock()
            mock_transport.start.side_effect = OSError("cannot start")
            mock_transport_cls.return_value = mock_transport

            # Must not raise
            await startup._start_servers()

        startup._ctx.services.tools.set_transport.assert_not_called()

    @pytest.mark.asyncio
    async def test_ondemand_stdio_server_skipped(self) -> None:
        cfg = _stdio_ondemand_cfg()
        startup = _make_startup({"lazy": cfg})

        with patch("agent.startup.StdioTransport", autospec=True) as mock_transport_cls:
            await startup._start_servers()

        mock_transport_cls.assert_not_called()
        startup._ctx.services.lifecycle.start_http_subprocess.assert_not_called()

    @pytest.mark.asyncio
    async def test_multiple_servers_all_processed(self) -> None:
        startup = _make_startup(
            {
                "http_srv": _http_subprocess_cfg(),
                "stdio_srv": _stdio_persistent_cfg(),
            }
        )

        with patch("agent.startup.StdioTransport", autospec=True) as mock_transport_cls:
            mock_transport = AsyncMock()
            mock_transport.start = AsyncMock()
            mock_transport_cls.return_value = mock_transport

            await startup._start_servers()

        startup._ctx.services.lifecycle.start_http_subprocess.assert_called_once()
        mock_transport.start.assert_called_once()


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

        mock_store = MagicMock()
        mock_store.find_latest_pending_approval.return_value = (
            "task-456",
            approval,
        )

        with patch("agent.startup.StateStore", return_value=mock_store):
            await startup._recover_pending_approvals()

        assert ctx.workflow.approval_pending is True
        assert ctx.turn.pending_approval_id == "approval-123"

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
        mock_store.find_latest_pending_approval.return_value = (
            "task-456",
            approval,
        )

        with patch("agent.startup.StateStore", return_value=mock_store):
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
        mock_store.find_latest_pending_approval.return_value = None

        with patch("agent.startup.StateStore", return_value=mock_store):
            await startup._recover_pending_approvals()

        assert ctx.workflow.approval_pending is False
        assert ctx.turn.pending_approval_id is None
        view.write_warning.assert_not_called()


# ── _setup_prompt() regression tests ────────────────────────────────────────────


class TestStartupOrchestratorSetupPrompt:
    """Regression tests for _setup_prompt() — pinned notes must NOT be injected."""

    @pytest.mark.asyncio
    async def test_no_pinned_notes_block_injected(self) -> None:
        """[Pinned Notes] block must NOT appear in system prompt."""
        ctx = MagicMock()
        ctx.services.memory = None  # memory disabled
        ctx.conv.system_prompt_name = "default"
        ctx.cfg.tool.system_prompts = {"default": "Initial prompt"}
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
        ctx.services.memory = mock_mem
        ctx.session.session_id = 1
        ctx.conv.system_prompt_name = "default"
        ctx.cfg.tool.system_prompts = {"default": "Initial prompt"}
        view = MagicMock()
        startup = StartupOrchestrator(ctx, view)

        await startup._setup_prompt()

        assert "[Relevant memories]" in ctx.conv.system_prompt_content
        assert "test memory" in ctx.conv.system_prompt_content

    @pytest.mark.asyncio
    async def test_no_memory_injection_when_disabled(self) -> None:
        """System prompt is unchanged when memory is disabled."""
        ctx = MagicMock()
        ctx.services.memory = None
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
        ctx.services.memory = None
        ctx.conv.system_prompt_name = "default"
        ctx.cfg.tool.system_prompts = {"default": "Initial prompt"}
        view = MagicMock()
        startup = StartupOrchestrator(ctx, view)

        await startup._setup_prompt()

        assert len(ctx.conv.history) == 1
        assert ctx.conv.history[0] == {"role": "system", "content": "Initial prompt"}
