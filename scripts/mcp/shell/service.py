#!/usr/bin/env python3
"""
shell_mcp_service.py
ShellService business logic and lazy singleton proxy for shell-mcp.

Dependency direction: shell_mcp_models → shell_mcp_service → shell_mcp_server
"""

from __future__ import annotations

import asyncio
import fnmatch
import logging
import os
import resource
import shlex
import shutil
import signal
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from mcp.server import ToolArgs
from mcp.shell.models import ShellRunRequest, ShellRunResponse, _get_cfg

# Standard library logger; log path is owned by shell_mcp_server.py
logger = logging.getLogger(__name__)


def _init_sandbox(backend: str) -> str:
    """Validate firejail availability at startup; fall back to 'none' if not found.

    Called once during ShellService.__init__ so the warning appears at startup
    rather than on every command execution.
    """
    if backend == "firejail":
        if shutil.which("firejail") is None:
            logger.warning(
                "firejail not found in PATH; shell_sandbox_backend falling back to 'none'"
            )
            return "none"
    return backend


def _set_resource_limits(max_memory_mb: int, timeout_sec: int) -> None:
    """Set resource limits in the child process via preexec_fn.

    Called inside the forked child before exec, so it affects only that process.
    Limits set:
      RLIMIT_CPU  — CPU time ceiling (2x timeout as a safety margin)
      RLIMIT_AS   — virtual address space (max_memory_mb)
      RLIMIT_NOFILE — open file descriptors
      RLIMIT_NPROC  — subprocess count (prevent fork bombs)
      RLIMIT_FSIZE  — written file size (prevent runaway writes)
    """
    mb = 1024 * 1024
    # CPU limit: 2x timeout_sec so asyncio timeout fires first under normal conditions
    cpu_limit = max(timeout_sec * 2, 60)
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
    # Address space: cap at max_memory_mb (soft == hard to make it a hard limit)
    mem_bytes = max_memory_mb * mb
    resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
    # File descriptors: generous but bounded to prevent descriptor leaks
    resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))
    # Subprocesses: allow a small number but block fork bombs
    resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
    # Write size: cap at 256 MB to prevent runaway writes
    fsize = 256 * mb
    resource.setrlimit(resource.RLIMIT_FSIZE, (fsize, fsize))


class ShellService:
    """Encapsulates sandboxed shell command execution with allowlist and resource limits."""

    def __init__(
        self,
        command_allowlist: list[str],
        shell_cwd_allowed_dirs: list[Path],
        shell_path: str,
        max_timeout_sec: int,
        max_output_kb: int,
        max_memory_mb: int,
        audit_log_path: str,
        sandbox_backend: str = "none",
        default_cwd: str = "",
        env_allowlist: list[str] | None = None,
        env_denylist: list[str] | None = None,
    ) -> None:
        # Normalize allowlist to base names only for consistent comparison
        self._allowlist: set[str] = {os.path.basename(c) for c in command_allowlist}
        self._cwd_allowed_dirs = shell_cwd_allowed_dirs
        self._path = shell_path
        self._max_timeout_sec = max_timeout_sec
        self._max_output_kb = max_output_kb
        self._max_memory_mb = max_memory_mb
        self._audit_log_path = audit_log_path
        # Validate firejail availability once at init; falls back to "none" if absent
        self._sandbox_backend = _init_sandbox(sandbox_backend)
        self._default_cwd = default_cwd
        self._env_allowlist: list[str] = (
            env_allowlist if env_allowlist is not None else []
        )
        self._env_denylist: list[str] = env_denylist if env_denylist is not None else []

    def _check_command(self, req: ShellRunRequest) -> list[str]:
        """Parse command and verify argv[0] is in the allowlist.

        When req.argv is provided it is used directly (prevents shell injection);
        otherwise req.command is split with shlex.split().
        Returns the validated argv list. Raises HTTPException 403/400 if not allowed.
        """
        if req.argv is not None:
            argv = req.argv
        else:
            try:
                argv = shlex.split(req.command)
            except ValueError as e:
                raise HTTPException(
                    status_code=400, detail=f"Invalid command string: {e}"
                )
        if not argv:
            raise HTTPException(status_code=400, detail="Empty command")
        # Compare base name to handle full-path commands like /usr/bin/ls
        base = os.path.basename(argv[0])
        if base not in self._allowlist:
            raise HTTPException(
                status_code=403,
                detail=f"Command not in allowlist: {base!r}",
            )
        return argv

    def _build_argv(self, argv: list[str]) -> list[str]:
        """Prepend firejail sandbox wrapper when sandbox_backend is 'firejail'."""
        if self._sandbox_backend != "firejail":
            return argv
        return ["firejail", "--private", "--net=none", "--noroot", "--"] + argv

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
            raise HTTPException(status_code=400, detail="Invalid cwd path")
        for allowed in self._cwd_allowed_dirs:
            try:
                resolved.relative_to(allowed.resolve())
                return str(resolved)
            except ValueError:
                continue
        raise HTTPException(
            status_code=403,
            detail="cwd is outside allowed directories",
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
        ts = datetime.now(tz=UTC).isoformat()
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

    async def run_command(self, req: ShellRunRequest) -> ShellRunResponse:
        """Execute the command in a sandboxed subprocess with resource limits.

        Steps:
          1. Parse and allowlist-check argv[0]
          2. Validate cwd
          3. Clamp timeout_sec and max_output_kb to server-configured maxima
          4. Launch subprocess with resource limits via preexec_fn
          5. Wait with asyncio timeout; kill on timeout
          6. Truncate combined stdout+stderr if over the output limit
          7. Write audit log
        """
        argv = self._check_command(req)
        # Preserve user-facing argv for audit log before prepending sandbox wrapper
        user_argv = argv[:]
        argv = self._build_argv(argv)
        cwd = self._resolve_cwd(req.cwd)

        # Clamp caller-supplied limits to server-configured maxima
        timeout_sec = min(req.timeout_sec, self._max_timeout_sec)
        max_output_bytes = min(req.max_output_kb, self._max_output_kb) * 1024

        # Filter caller env vars, then merge: inherit current env, override PATH
        filtered_env = self._filter_env(req.env)
        env = {**os.environ, "PATH": self._path, **filtered_env}

        max_memory_mb = self._max_memory_mb

        start = time.monotonic()
        timed_out = False

        proc = await asyncio.create_subprocess_exec(
            *argv,
            stdin=asyncio.subprocess.DEVNULL,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd,
            env=env,
            # start_new_session=True creates a new process group so we can
            # kill the entire group (including children) on timeout
            start_new_session=True,
            preexec_fn=lambda: _set_resource_limits(max_memory_mb, timeout_sec),
        )

        try:
            stdout_b, stderr_b = await asyncio.wait_for(
                proc.communicate(), timeout=timeout_sec
            )
        except TimeoutError:
            timed_out = True
            # Kill the entire process group; ignore errors if already dead
            try:
                os.killpg(proc.pid, signal.SIGTERM)
            except OSError:
                pass
            # Wait up to 2 s for graceful exit before escalating to SIGKILL
            try:
                await asyncio.wait_for(proc.wait(), timeout=2.0)
            except TimeoutError:
                try:
                    os.killpg(proc.pid, signal.SIGKILL)
                except OSError:
                    pass
                try:
                    await asyncio.wait_for(proc.wait(), timeout=5.0)
                except TimeoutError:
                    pass
            stdout_b = b""
            stderr_b = b""

        elapsed = time.monotonic() - start
        exit_code = proc.returncode if proc.returncode is not None else -1

        # Truncate combined output if total exceeds the byte limit; slice bytes
        # before decoding so multibyte characters do not inflate the count
        truncated = False
        combined_bytes = len(stdout_b) + len(stderr_b)
        if combined_bytes > max_output_bytes:
            truncated = True
            # Allocate quota proportionally between stdout and stderr
            half = max_output_bytes // 2
            stdout_b = stdout_b[:half]
            stderr_b = stderr_b[:half]

        # Decode bytes to strings; replace undecodable bytes to avoid HTTPException
        stdout = stdout_b.decode("utf-8", errors="replace")
        stderr = stderr_b.decode("utf-8", errors="replace")

        self._write_audit_log(
            req.command, user_argv, cwd, exit_code, elapsed, truncated
        )

        return ShellRunResponse(
            stdout=stdout,
            stderr=stderr,
            exit_code=exit_code,
            timed_out=timed_out,
            truncated=truncated,
            elapsed_sec=round(elapsed, 3),
        )

    # ── Dispatch handlers: format service results as plain text for the LLM ──

    async def fmt_run_command(self, args: ToolArgs) -> str:
        result = await self.run_command(ShellRunRequest(**args))
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


class _LazyShellService:
    """Lazy singleton proxy: defers ShellService init until first attribute access."""

    _instance: ShellService | None = None

    def __getattr__(self, name: str) -> Any:
        if _LazyShellService._instance is None:
            cfg = _get_cfg()
            allowed_dirs = [Path(d) for d in cfg.get("shell_cwd_allowed_dirs", [])]
            if not allowed_dirs:
                logger.warning(
                    "shell_cwd_allowed_dirs is empty — all cwd values will be rejected"
                )
            allowlist = cfg.get("command_allowlist", [])
            if not allowlist:
                logger.warning(
                    "command_allowlist is empty — all commands will be rejected"
                )
            _LazyShellService._instance = ShellService(
                command_allowlist=allowlist,
                shell_cwd_allowed_dirs=allowed_dirs,
                shell_path=cfg.get("shell_path", "/usr/local/bin:/usr/bin:/bin"),
                max_timeout_sec=cfg.get("max_timeout_sec", 300),
                max_output_kb=cfg.get("max_output_kb", 4096),
                max_memory_mb=cfg.get("max_memory_mb", 512),
                audit_log_path=cfg.get(
                    "audit_log_path", "/opt/llm/logs/shell_audit.log"
                ),
                sandbox_backend=cfg.get("shell_sandbox_backend", "none"),
                default_cwd=cfg.get("default_cwd", ""),
                env_allowlist=cfg.get("env_allowlist", []),
                env_denylist=cfg.get("env_denylist", []),
            )
        return getattr(_LazyShellService._instance, name)


# Singleton proxy; actual ShellService is created on first attribute access
_service: ShellService = _LazyShellService()  # type: ignore[assignment]
