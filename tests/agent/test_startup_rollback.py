"""Behavior-lock tests for StartupOrchestrator.run() rollback behavior.

Tests that lifecycle.shutdown_all() is called when _start_servers() succeeds before failure.
"""

from __future__ import annotations

import subprocess
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from agent.startup import StartupInterrupted, StartupOrchestrator
from agent.startup_component_init import ComponentInitializer
from shared.mcp_config import (
    McpServerConfig,
    SecurityProfile,
    StartupMode,
    TransportType,
)

# ── Helpers ───────────────────────────────────────────────────────────────────


def _http_subprocess_cfg() -> McpServerConfig:
    return McpServerConfig(
        transport=TransportType.HTTP,
        url="http://127.0.0.1:9999",
        auth_token="test-token",
        startup_mode=StartupMode.SUBPROCESS,
        cmd=["echo", "hello"],
    )


def _make_rollback_startup() -> tuple[StartupOrchestrator, AsyncMock]:
    """Return (orchestrator, mock_lifecycle) with _initialize patched to a no-op."""
    ctx = MagicMock()
    ctx.cfg.obs.audit_log_file = "/opt/llm/logs/audit.log"
    ctx.cfg.rag.embed_url = "http://localhost:6000/embedding"
    mock_lifecycle = AsyncMock()
    ctx.services_required.lifecycle = mock_lifecycle
    view = MagicMock()
    orch = StartupOrchestrator(ctx, view)
    orch._initialize = MagicMock()
    return orch, mock_lifecycle


class TestStartupRollback:
    """run() calls lifecycle.shutdown_all() iff _start_servers() succeeded before failure."""

    @pytest.mark.asyncio
    async def test_rollback_on_check_services_failure(self) -> None:
        orch, mock_lifecycle = _make_rollback_startup()
        orch._start_servers = AsyncMock()
        orch._check_services = AsyncMock(
            side_effect=RuntimeError("health check failed")
        )
        orch._recover_pending_approvals = AsyncMock()
        orch._setup_prompt = AsyncMock()

        with pytest.raises(RuntimeError, match="health check failed"):
            await orch.run()

        mock_lifecycle.shutdown_all.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rollback_on_recover_pending_failure(self) -> None:
        orch, mock_lifecycle = _make_rollback_startup()
        orch._start_servers = AsyncMock()
        orch._check_services = AsyncMock()
        orch._recover_pending_approvals = AsyncMock(
            side_effect=RuntimeError("approval recovery failed")
        )
        orch._setup_prompt = AsyncMock()

        with pytest.raises(RuntimeError, match="approval recovery failed"):
            await orch.run()

        mock_lifecycle.shutdown_all.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rollback_shutdown_failure_preserves_original_error(self) -> None:
        orch, mock_lifecycle = _make_rollback_startup()
        orch._start_servers = AsyncMock()
        orch._check_services = AsyncMock(side_effect=RuntimeError("original error"))
        orch._recover_pending_approvals = AsyncMock()
        orch._setup_prompt = AsyncMock()
        mock_lifecycle.shutdown_all.side_effect = OSError("shutdown failed")

        with pytest.raises(RuntimeError, match="original error"):
            await orch.run()

    @pytest.mark.asyncio
    async def test_no_rollback_on_initialize_failure(self) -> None:
        orch, mock_lifecycle = _make_rollback_startup()
        orch._check_services = AsyncMock()
        orch._recover_pending_approvals = AsyncMock()
        orch._setup_prompt = AsyncMock()

        with patch.object(
            ComponentInitializer, "initialize", side_effect=RuntimeError("init failed")
        ):
            with pytest.raises(RuntimeError, match="init failed"):
                await orch.run()

        mock_lifecycle.shutdown_all.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_rollback_on_start_servers_failure(self) -> None:
        orch, mock_lifecycle = _make_rollback_startup()
        orch._start_servers = AsyncMock(side_effect=RuntimeError("server start failed"))
        orch._check_services = AsyncMock()

        with pytest.raises(RuntimeError, match="server start failed"):
            await orch.run()

        mock_lifecycle.shutdown_all.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rollback_on_partial_multi_server_failure(self) -> None:
        """run() rolls back via shutdown_all() after a two-server startup where the
        first server starts successfully and the second fails on both the first
        attempt and the retry — the second server's retry failure makes
        `_start_servers()` itself raise mid-loop (after `first_proc` was already
        appended), exercising "one subprocess already started before the failure
        that triggers rollback" from the plan's Goal.
        """
        ctx = MagicMock()
        ctx.cfg.mcp.security_profile = SecurityProfile.PRODUCTION
        ctx.cfg.mcp.mcp_servers = {
            "first": _http_subprocess_cfg(),
            "second": _http_subprocess_cfg(),
        }
        ctx.cfg.obs.audit_log_file = "/opt/llm/logs/audit.log"
        ctx.cfg.rag.embed_url = "http://localhost:6000/embedding"
        ctx.services_required.tools = MagicMock()
        mock_lifecycle = AsyncMock()
        ctx.services_required.lifecycle = mock_lifecycle
        first_proc = MagicMock(spec=subprocess.Popen)
        mock_lifecycle.start_http_subprocess = AsyncMock(
            side_effect=[
                first_proc,
                RuntimeError("port busy"),
                RuntimeError("port busy"),
            ]
        )
        view = MagicMock()
        orch = StartupOrchestrator(ctx, view)
        orch._initialize = MagicMock()
        orch._check_services = AsyncMock(side_effect=RuntimeError("downstream failure"))
        orch._recover_pending_approvals = AsyncMock()
        orch._setup_prompt = AsyncMock()

        with pytest.raises(RuntimeError):
            await orch.run()

        mock_lifecycle.shutdown_all.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_rollback_no_op_when_no_subprocess_started(self) -> None:
        """run() still rolls back (safe no-op shutdown_all()) when _start_servers()
        raises before any subprocess is spawned."""
        orch, mock_lifecycle = _make_rollback_startup()
        orch._start_servers = AsyncMock(
            side_effect=RuntimeError("no servers configured")
        )
        orch._check_services = AsyncMock()

        with pytest.raises(RuntimeError, match="no servers configured"):
            await orch.run()

        mock_lifecycle.shutdown_all.assert_awaited_once()
        assert orch._spawned_subprocesses == []

    @pytest.mark.asyncio
    async def test_run_populates_spawned_subprocesses_on_exception_path(self) -> None:
        """Regression: _spawned_subprocesses must be populated even when run() raises."""
        orch, mock_lifecycle = _make_rollback_startup()
        fake_procs = [
            MagicMock(spec=subprocess.Popen),
            MagicMock(spec=subprocess.Popen),
        ]
        orch._start_servers = AsyncMock(return_value=fake_procs)
        orch._check_services = AsyncMock(
            side_effect=RuntimeError("health check failed")
        )
        orch._recover_pending_approvals = AsyncMock()
        orch._setup_prompt = AsyncMock()
        mock_lifecycle.shutdown_all.side_effect = OSError("shutdown failed")

        with pytest.raises(RuntimeError, match="health check failed"):
            await orch.run()

        assert orch._spawned_subprocesses == fake_procs

    @pytest.mark.asyncio
    async def test_run_returns_spawned_subprocesses_on_success(self) -> None:
        """Assert run()'s third return value equals the real spawned-process list."""
        orch, mock_lifecycle = _make_rollback_startup()
        fake_procs = [
            MagicMock(spec=subprocess.Popen),
            MagicMock(spec=subprocess.Popen),
        ]
        orch._start_servers = AsyncMock(return_value=fake_procs)
        orch._check_services = AsyncMock()
        orch._recover_pending_approvals = AsyncMock()
        orch._setup_prompt = AsyncMock()
        orch._cmds = MagicMock()
        orch._orchestrator = MagicMock()

        cmds, orchestrator, spawned = await orch.run()

        assert spawned == fake_procs

    @pytest.mark.asyncio
    async def test_startup_interrupted_triggers_rollback_like_any_other_exception(
        self,
    ) -> None:
        """StartupInterrupted must flow through run()'s existing rollback
        `except Exception as setup_err:` block unchanged — no dedicated branch."""
        orch, mock_lifecycle = _make_rollback_startup()
        orch._start_servers = AsyncMock(
            side_effect=StartupInterrupted("shutdown requested")
        )

        with pytest.raises(StartupInterrupted, match="shutdown requested"):
            await orch.run()

        mock_lifecycle.shutdown_all.assert_awaited_once()
