#!/usr/bin/env python3
"""mcp_servers/shell/subprocess_runner.py

Subprocess execution logic for shell-mcp.

Dependency direction: mcp_servers.shell.subprocess_runner → shared.protocols.shell
Import from here:  from mcp_servers.shell.subprocess_runner import SubprocessRunner
"""

from __future__ import annotations

import asyncio
import os
import signal

from .service_static_helpers import make_preexec


class SubprocessRunner:
    """Handles subprocess creation, timeout killing, and output truncation."""

    def __init__(
        self,
        sandbox_backend: str,
        max_memory_mb: int,
        timeout_sec: int,
        exec_uid: int | None,
        exec_gid: int | None,
    ) -> None:
        """Initialize the subprocess runner with sandbox configuration and resource limits."""
        self._sandbox_backend = sandbox_backend
        self._max_memory_mb = max_memory_mb
        self._timeout_sec = timeout_sec
        self._exec_uid = exec_uid
        self._exec_gid = exec_gid

    def build_argv(self, argv: list[str]) -> list[str]:
        """Prepend firejail sandbox wrapper when sandbox_backend is 'firejail'."""
        if self._sandbox_backend != "firejail":
            return argv
        return ["firejail", "--private", "--net=none", "--noroot", "--"] + argv

    async def kill_timed_out_process(self, proc: asyncio.subprocess.Process) -> None:
        """Send SIGTERM/SIGKILL to the process group after a timeout."""
        # NOTE: kill_policy and kill_grace_sec must be passed at call site
        # This is intentionally kept minimal; caller handles policy dispatch
        try:
            os.killpg(proc.pid, signal.SIGKILL)
        except OSError:
            pass

    async def run_subprocess(
        self,
        argv: list[str],
        cwd: str | None,
        env: dict[str, str],
        timeout_sec: int,
        kill_policy: str,
        kill_grace_sec: float,
    ) -> tuple[asyncio.subprocess.Process, bytes, bytes, bool]:
        """Launch subprocess and wait with timeout; kill on TimeoutError.

        Returns (process, stdout, stderr, timed_out).
        """
        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
            start_new_session=True,
            preexec_fn=make_preexec(
                self._max_memory_mb, timeout_sec, self._exec_uid, self._exec_gid
            ),
        )
        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(),
                timeout=timeout_sec,
            )
        except TimeoutError:
            await self._kill_timed_out_process(proc, kill_policy, kill_grace_sec)
            return proc, b"", b"", True
        return proc, stdout_b, stderr_b, False

    async def _kill_timed_out_process(
        self, proc: asyncio.subprocess.Process, kill_policy: str, grace: float
    ) -> None:
        """Send SIGTERM/SIGKILL to the process group after a timeout."""
        if kill_policy == "sigkill_only":
            try:
                os.killpg(proc.pid, signal.SIGKILL)
            except OSError:
                pass
        else:
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except OSError:
                pass
            try:
                await asyncio.wait_for(proc.wait(), timeout=grace)
            except TimeoutError:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except OSError:
                    pass
        try:
            await asyncio.wait_for(proc.wait(), timeout=5.0)
        except TimeoutError:
            pass

    @staticmethod
    def truncate_output(
        stdout_b: bytes, stderr_b: bytes, max_output_bytes: int
    ) -> tuple[bytes, bytes, bool]:
        """Split max_output_bytes evenly between stdout and stderr; return (stdout, stderr, truncated)."""
        if len(stdout_b) + len(stderr_b) <= max_output_bytes:
            return stdout_b, stderr_b, False
        half = max_output_bytes // 2
        return stdout_b[:half], stderr_b[:half], True
