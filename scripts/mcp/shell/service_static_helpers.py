#!/usr/bin/env python3
"""mcp/shell/service_static_helpers.py

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


def init_sandbox(backend: str) -> str:
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
    mb = 1024 * 1024
    cpu_limit = max(timeout_sec * 2, 60)
    resource.setrlimit(resource.RLIMIT_CPU, (cpu_limit, cpu_limit))
    mem_bytes = max_memory_mb * mb
    resource.setrlimit(resource.RLIMIT_AS, (mem_bytes, mem_bytes))
    resource.setrlimit(resource.RLIMIT_NOFILE, (256, 256))
    resource.setrlimit(resource.RLIMIT_NPROC, (64, 64))
    fsize = 256 * mb
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
        if gid is not None:
            os.setgid(gid)
        if uid is not None:
            os.setuid(uid)
        set_resource_limits(max_memory_mb, timeout_sec)

    return _preexec
