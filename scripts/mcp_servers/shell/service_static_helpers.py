#!/usr/bin/env python3
"""scripts/mcp_servers/shell/service_static_helpers.py

Static helper functions for ShellService, extracted to reduce service.py size.

These helpers have no instance state — they operate purely on their arguments.
"""

from __future__ import annotations

import logging
import os
import resource
import shutil
from collections.abc import Callable

logger = logging.getLogger(__name__)

# RLIMIT_CPU: CPU time ceiling in seconds, computed as timeout_sec * multiplier,
# floored at a minimum so short timeouts still get a workable CPU budget.
_CPU_LIMIT_SAFETY_MULTIPLIER = 2
_MIN_CPU_LIMIT_SEC = 60
_BYTES_PER_MB = 1024 * 1024
# RLIMIT_NOFILE: max open file descriptors.
_MAX_OPEN_FILE_DESCRIPTORS = 256
# RLIMIT_NPROC: max subprocess/thread count (prevents fork bombs).
_MAX_SUBPROCESS_COUNT = 64
# RLIMIT_FSIZE: max size of any file written by the child, in megabytes.
_MAX_WRITTEN_FILE_MB = 256


def init_sandbox(backend: str) -> str:
    """Validate that the sandbox backend binary exists; returns the backend name unchanged."""
    if backend == "firejail" and shutil.which("firejail") is None:
        raise RuntimeError(
            "shell_sandbox_backend=firejail is configured but firejail is not found in PATH"
        )
    return backend


def set_resource_limits(max_memory_mb: int, timeout_sec: int) -> None:
    """Set resource limits in the child process via preexec_fn.

    Limits set:
      RLIMIT_CPU  — CPU time ceiling (2x timeout as a safety margin)
      RLIMIT_AS   — virtual address space (max_memory_mb)
      RLIMIT_NOFILE — open file descriptors
      RLIMIT_NPROC  — subprocess count (prevent fork bombs)
      RLIMIT_FSIZE  — written file size (prevent runaway writes)
    """
    cpu_limit = max(timeout_sec * _CPU_LIMIT_SAFETY_MULTIPLIER, _MIN_CPU_LIMIT_SEC)
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
    mem_bytes = max_memory_mb * _BYTES_PER_MB
    resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
    resource.setrlimit(
        resource.RLIMIT_NOFILE, (_MAX_OPEN_FILE_DESCRIPTORS, _MAX_OPEN_FILE_DESCRIPTORS)
    )
    resource.setrlimit(
        resource.RLIMIT_NPROC, (_MAX_SUBPROCESS_COUNT, _MAX_SUBPROCESS_COUNT)
    )
    fsize = _MAX_WRITTEN_FILE_MB * _BYTES_PER_MB
    resource.setrlimit(resource.RLIMIT_FSIZE, (fsize, fsize))


def make_preexec(
    max_memory_mb: int,
    timeout_sec: int,
    uid: int | None,
    gid: int | None,
) -> Callable[[], None]:
    """Build preexec_fn for the child process.

    Optionally switches OS user (setgid then setuid) when uid/gid are provided.
    Always applies resource limits. No logging here — called in forked child.
    """

    def _preexec() -> None:
        """Apply group/user switching and resource limits before subprocess execution."""
        if gid is not None:
            os.setgid(gid)
        if uid is not None:
            os.setuid(uid)
        set_resource_limits(max_memory_mb, timeout_sec)

    return _preexec
