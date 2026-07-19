#!/usr/bin/env python3
"""mcp_servers/shell/service.py

ShellService business logic and lazy singleton proxy for shell-mcp.

Dependency direction: shell_mcp_models -> shell_mcp_service -> shell_mcp_server

Split layout:
  service_static_helpers.py — Pure static helpers (sandbox, resource limits, preexec)
  service.py                — ShellService class + dispatch table factory + build_service
"""

from __future__ import annotations

import asyncio
import fnmatch
import logging
import os
import pwd
import shlex
import time
from collections.abc import Awaitable, Callable
from pathlib import Path

from shared.json_utils import dumps as _json_dumps
from shared.json_utils import now_iso_raw
from shared.protocols.shell import ShellPolicy

from mcp_servers.server import ToolArgs
from mcp_servers.shell.shell_models import (
    ShellAuthorizationError,
    ShellRunRequest,
    ShellRunResponse,
    ShellValidationError,
)

from .service_static_helpers import (
    init_sandbox,
)
from .subprocess_runner import SubprocessRunner

# Standard library logger; log path is owned by shell_mcp_server.py
logger = logging.getLogger(__name__)


class ShellService:
    """Encapsulates sandboxed shell command execution with allowlist and resource limits."""

    def __init__(self, policy: ShellPolicy) -> None:
        """Initialize with shell policy including commands, paths, and resource limits."""
        self._policy = policy
        # Normalize allowlist to base names only for consistent comparison
        self._allowlist: set[str] = {
            os.path.basename(c) for c in policy.allowed_commands
        }
        self._cwd_allowed_dirs = [Path(d) for d in policy.cwd_allowed_dirs]
        self._path = policy.shell_path
        self._max_timeout_sec = policy.timeout_sec
        self._max_output_kb = policy.max_output_kb
        self._max_memory_mb = policy.max_memory_mb
        self._audit_log_path = policy.audit_log_path
        # Validate firejail availability once at init; falls back to "none" if absent
        self._sandbox_backend = init_sandbox(policy.sandbox_backend)
        self._default_cwd = policy.default_cwd
        self._env_allowlist: list[str] = list(policy.env_allowlist)
        self._env_denylist: list[str] = list(policy.env_denylist)
        # Resolve execution_user to uid/gid at init time to avoid pwd lookup in child
        self._exec_uid: int | None = None
        self._exec_gid: int | None = None
        if policy.execution_user:
            if os.getuid() != 0:
                # Non-root cannot call setuid; log warning and continue as current user
                logger.warning(
                    "execution_user=%r requires CAP_SETUID (root); user switch is disabled",
                    policy.execution_user,
                )
            else:
                try:
                    pw = pwd.getpwnam(policy.execution_user)
                    self._exec_uid = pw.pw_uid
                    self._exec_gid = pw.pw_gid
                except KeyError:
                    logger.warning(
                        "execution_user=%r not found in /etc/passwd; user switch is disabled",
                        policy.execution_user,
                    )
        self._subprocess_runner = SubprocessRunner(
            sandbox_backend=self._sandbox_backend,
            max_memory_mb=self._max_memory_mb,
            timeout_sec=self._max_timeout_sec,
            exec_uid=self._exec_uid,
            exec_gid=self._exec_gid,
        )

    @property
    def sandbox_backend(self) -> str:
        """Return the resolved sandbox backend ('firejail' or 'none')."""
        return self._sandbox_backend

    def _check_command(self, req: ShellRunRequest) -> list[str]:
        """Parse command and verify argv[0] is in the allowlist.

        When req.argv is provided it is used directly (prevents shell injection);
        otherwise req.command is split with shlex.split().
        Returns the validated argv list. Raises domain exceptions if not allowed.
        """
        if req.argv is not None:
            argv = req.argv
        else:
            try:
                argv = shlex.split(req.command)
            except ValueError as e:
                raise ShellValidationError(
                    f"Invalid command string: {e}",
                )
        if not argv:
            raise ShellValidationError("Empty command")
        # Compare base name to handle full-path commands like /usr/bin/ls
        base = os.path.basename(argv[0])
        if base not in self._allowlist:
            raise ShellAuthorizationError(
                f"Command not in allowlist: {base!r}",
            )
        result: list[str] = argv
        return result

    def _filter_env(self, req_env: dict[str, str]) -> dict[str, str]:
        """Filter caller-supplied environment variables.

        When env_allowlist is non-empty, only keys in the allowlist are kept.
        Otherwise, keys matching any env_denylist glob pattern are removed.
        """
        if self._env_allowlist:
            return {k: v for k, v in req_env.items() if k in self._env_allowlist}
        if self._env_denylist:
            return {
                k: v
                for k, v in req_env.items()
                if not any(fnmatch.fnmatch(k, p) for p in self._env_denylist)
            }
        return req_env

    def _resolve_cwd(self, raw_cwd: str | None) -> str | None:
        """Validate cwd is under one of shell_cwd_allowed_dirs; raise 403 if not.

        Falls back to default_cwd when raw_cwd is None and default_cwd is configured.
        Returns None when no default is configured (inherit parent cwd).
        """
        if raw_cwd is None:
            if not self._default_cwd:
                return None
            raw_cwd = self._default_cwd
        try:
            resolved = Path(raw_cwd).resolve()
        except OSError:
            raise ShellValidationError("Invalid cwd path")
        for allowed in self._cwd_allowed_dirs:
            try:
                resolved.relative_to(allowed.resolve())
                return str(resolved)
            except ValueError:
                continue
        raise ShellAuthorizationError(
            "cwd is outside allowed directories",
        )

    def _write_audit_log(
        self,
        command: str,
        argv: list[str],
        cwd: str | None,
        exit_code: int,
        elapsed: float,
        truncated: bool,
    ) -> None:
        """Append a single audit record to the shell audit log.

        Writing errors are logged but never propagated — audit failure must not
        block the caller from receiving the command result.
        """
        ts = now_iso_raw()
        record = (
            f"{ts} cmd={command!r} argv={argv!r} cwd={cwd!r}"
            f" uid={os.getuid()} exit={exit_code}"
            f" elapsed={elapsed:.2f}s truncated={truncated}\n"
        )
        try:
            with open(self._audit_log_path, "a", encoding="utf-8") as fh:
                fh.write(record)
        except OSError as e:
            logger.error("_write_audit_log: failed to write audit log: %s", e)

    async def _kill_timed_out_process(self, proc: asyncio.subprocess.Process) -> None:
        """Send SIGTERM/SIGKILL to the process group after a timeout."""
        await self._subprocess_runner.kill_timed_out_process(proc)

    async def _run_subprocess(
        self,
        argv: list[str],
        cwd: str | None,
        env: dict[str, str],
        timeout_sec: int,
    ) -> tuple[asyncio.subprocess.Process, bytes, bytes, bool]:
        """Launch subprocess and wait with timeout; kill on TimeoutError.

        Returns (process, stdout, stderr, timed_out).
        """
        return await self._subprocess_runner.run_subprocess(
            argv,
            cwd,
            env,
            timeout_sec,
            self._policy.kill_policy,
            self._policy.kill_grace_sec,
        )

    @staticmethod
    def _build_run_response(
        req: ShellRunRequest,
        proc: asyncio.subprocess.Process,
        stdout: str,
        stderr: str,
        timed_out: bool,
        truncated: bool,
        elapsed: float,
    ) -> ShellRunResponse:
        """Build a ShellRunResponse from execution results."""
        exit_code = proc.returncode if proc.returncode is not None else -1
        return ShellRunResponse(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            timed_out=timed_out,
            truncated=truncated,
            elapsed_sec=round(elapsed, 3),
        )

    async def run_command(self, req: ShellRunRequest) -> ShellRunResponse:
        """Execute the command in a sandboxed subprocess with resource limits.

        Steps:
          1. Parse and allowlist-check argv[0]
          2. Validate cwd
          3. Clamp timeout_sec and max_output_kb to server-configured maxima
          4. Launch subprocess with resource limits via preexec_fn
          5. Wait with asyncio timeout; kill on timeout using configured kill_policy
          6. Truncate combined stdout+stderr if over the output limit
          7. Write audit log
        """
        argv = self._check_command(req)
        # Preserve user-facing argv for audit log before prepending sandbox wrapper
        user_argv = argv[:]
        argv = self._subprocess_runner.build_argv(argv)
        cwd = self._resolve_cwd(req.cwd)

        # Clamp caller-supplied limits to server-configured maxima
        timeout_sec = min(req.timeout_sec, self._max_timeout_sec)
        max_output_bytes = min(req.max_output_kb, self._max_output_kb) * 1024

        # Filter caller env vars, then merge: inherit current env, override PATH
        filtered_env = self._filter_env(req.env)
        env = {**os.environ, "PATH": self._path, **filtered_env}

        start = time.monotonic()
        proc, stdout_b, stderr_b, timed_out = await self._run_subprocess(
            argv, cwd, env, timeout_sec
        )
        elapsed = time.monotonic() - start

        # Slice bytes before decoding so multibyte characters do not inflate the count
        stdout_b, stderr_b, truncated = self._subprocess_runner.truncate_output(
            stdout_b, stderr_b, max_output_bytes
        )

        # Decode bytes to strings; replace undecodable bytes to avoid decode errors
        stdout = stdout_b.decode("utf-8", errors="replace")
        stderr = stderr_b.decode("utf-8", errors="replace")

        self._write_audit_log(
            req.command,
            user_argv,
            cwd,
            proc.returncode if proc.returncode is not None else -1,
            elapsed,
            truncated,
        )

        return self._build_run_response(
            req, proc, stdout, stderr, timed_out, truncated, elapsed
        )

    # ── Dispatch handlers: format service results as plain text for the LLM ──

    async def fmt_run_command(self, args: ToolArgs) -> str:
        """Execute a shell command via the service and format the result as plain text."""
        req = ShellRunRequest(**args)
        if req.dry_run:
            cwd = req.cwd or "(default)"
            cmd_display = req.command
            preview = f"Would execute: {cmd_display} (cwd: {cwd})"
            dry_result: str = _json_dumps({"preview": preview, "dry_run": True})
            return dry_result
        result = await self.run_command(req)
        return self._format_run_result(result)

    @staticmethod
    def _format_run_result(
        result: ShellRunResponse,
    ) -> str:
        """Format a ShellRunResponse as plain text for the LLM."""
        parts: list[str] = []
        if result.timed_out:
            parts.append("[TIMED OUT]")
        parts.append(f"exit_code={result.exit_code} elapsed={result.elapsed_sec}s")
        if result.truncated:
            parts.append("[OUTPUT TRUNCATED]")
        if result.stdout:
            parts.append(f"--- stdout ---\n{result.stdout}")
        if result.stderr:
            parts.append(f"--- stderr ---\n{result.stderr}")
        return "\n".join(parts)

    def get_dispatch_table(
        self,
    ) -> dict[str, Callable[[ToolArgs], Awaitable[str]]]:
        """Build and return the MCP tool dispatch table keyed by tool name."""
        return {
            "shell_run": self.fmt_run_command,
        }


def build_service(policy: ShellPolicy) -> ShellService:
    """Construct a ShellService from a ShellPolicy object."""
    if not policy.cwd_allowed_dirs:
        logger.warning(
            "shell_cwd_allowed_dirs is empty — all cwd values will be rejected",
        )
    if not policy.allowed_commands:
        logger.warning(
            "command_allowlist is empty — all commands will be rejected",
        )
    return ShellService(policy)
