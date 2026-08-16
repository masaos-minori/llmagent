"""
tests/mcp_servers/shell/test_subprocess_runner.py
Characterization tests for SubprocessRunner's kill-signal and timeout-escalation
paths that are not exercised via ShellService.run_command() (see TestKillPolicy
in test_shell_mcp_service.py for the through-service, happy-path coverage).

These tests lock the following pre-existing behavior in
mcp_servers/shell/subprocess_runner.py:
  - kill_timed_out_process (public): unconditional SIGKILL to the process group,
    OSError swallowed (process already gone).
  - _kill_timed_out_process (private, policy-aware): sigkill_only sends SIGKILL
    only; sigterm_then_sigkill sends SIGTERM first, escalates to SIGKILL if the
    grace-period wait times out; OSError is swallowed at every killpg call site;
    the final safety-net wait is bounded and swallows TimeoutError.
"""

from __future__ import annotations

import signal
from unittest.mock import AsyncMock, MagicMock, call, patch

import pytest
from mcp_servers.shell.subprocess_runner import SubprocessRunner

# ── Fixtures ──────────────────────────────────────────────────────────────────


def _make_runner() -> SubprocessRunner:
    return SubprocessRunner(
        sandbox_backend="none",
        max_memory_mb=256,
        timeout_sec=30,
        exec_uid=None,
        exec_gid=None,
    )


def _make_proc(pid: int) -> MagicMock:
    proc = MagicMock()
    proc.pid = pid
    proc.wait = AsyncMock(return_value=0)
    return proc


# ── kill_timed_out_process (public) ────────────────────────────────────────────


class TestKillTimedOutProcessPublic:
    @pytest.mark.asyncio
    async def test_sends_sigkill_to_process_group(self) -> None:
        runner = _make_runner()
        proc = _make_proc(pid=555)
        with patch("os.killpg") as mock_killpg:
            await runner.kill_timed_out_process(proc)
        mock_killpg.assert_called_once_with(555, signal.SIGKILL)

    @pytest.mark.asyncio
    async def test_swallows_oserror_when_process_already_gone(self) -> None:
        runner = _make_runner()
        proc = _make_proc(pid=556)
        with patch("os.killpg", side_effect=OSError("no such process")):
            await runner.kill_timed_out_process(proc)  # must not raise


# ── _kill_timed_out_process (private, policy-aware) ────────────────────────────


class TestKillTimedOutProcessPrivate:
    @pytest.mark.asyncio
    async def test_sigkill_only_swallows_oserror(self) -> None:
        runner = _make_runner()
        proc = _make_proc(pid=600)
        with patch("os.killpg", side_effect=OSError("gone")):
            await runner._kill_timed_out_process(proc, "sigkill_only", 2.0)

    @pytest.mark.asyncio
    async def test_sigterm_then_sigkill_swallows_oserror_on_sigterm(self) -> None:
        runner = _make_runner()
        proc = _make_proc(pid=601)
        with patch("os.killpg", side_effect=OSError("gone")) as mock_killpg:
            await runner._kill_timed_out_process(proc, "sigterm_then_sigkill", 2.0)
        mock_killpg.assert_called_once_with(601, signal.SIGTERM)

    @pytest.mark.asyncio
    async def test_escalates_to_sigkill_when_grace_period_expires(self) -> None:
        runner = _make_runner()
        proc = _make_proc(pid=602)
        proc.wait = AsyncMock(side_effect=[TimeoutError(), 0])
        with patch("os.killpg") as mock_killpg:
            await runner._kill_timed_out_process(proc, "sigterm_then_sigkill", 0.01)
        assert mock_killpg.call_args_list == [
            call(602, signal.SIGTERM),
            call(602, signal.SIGKILL),
        ]

    @pytest.mark.asyncio
    async def test_escalation_sigkill_oserror_is_swallowed(self) -> None:
        runner = _make_runner()
        proc = _make_proc(pid=603)
        proc.wait = AsyncMock(side_effect=[TimeoutError(), 0])
        with patch("os.killpg", side_effect=[None, OSError("gone")]):
            await runner._kill_timed_out_process(proc, "sigterm_then_sigkill", 0.01)

    @pytest.mark.asyncio
    async def test_final_safety_wait_timeout_is_swallowed(self) -> None:
        runner = _make_runner()
        proc = _make_proc(pid=604)
        proc.wait = AsyncMock(side_effect=TimeoutError())
        with patch("os.killpg"):
            await runner._kill_timed_out_process(proc, "sigkill_only", 2.0)
