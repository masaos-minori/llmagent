#!/usr/bin/env python3
"""scripts/mcp_servers/shell/shell_service_static_helpers.py

Static helper functions for ShellService, extracted to reduce service.py size.

These helpers have no instance state — they operate purely on their arguments.
validate_shell_security() is a pure function of its arguments for the same reason.
"""

from __future__ import annotations

import logging
import os
import resource
import shutil
from collections.abc import Callable, Mapping, Sequence

from shared.security.result_dto import (
    REASON_ALLOWLIST_EMPTY,
    REASON_CONFIG_INVALID,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    REASON_SANDBOX_BACKEND_MISSING,
    REASON_SANDBOX_BACKEND_UNSUPPORTED,
    SecurityCheckResult,
    SecurityCheckStatus,
)

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


# Environment a sandboxed command may inherit from the server process. Everything else,
# in particular the MCP Bearer tokens and GITHUB_TOKEN the Agent hands to this process, is
# withheld so model-chosen commands cannot read credentials.
_BASE_ENV_KEYS = frozenset(
    {"HOME", "USER", "LOGNAME", "SHELL", "LANG", "TMPDIR", "TMP", "TEMP"}
)
_BASE_ENV_PREFIXES = ("LC_",)
# Matched on `_`-delimited segments so TOKENIZERS_PARALLELISM is kept.
_SECRET_ENV_SEGMENTS = frozenset(
    {"TOKEN", "SECRET", "PASSWORD", "PASSWD", "CREDENTIAL", "CREDENTIALS", "APIKEY"}
)

_SANDBOX_BACKEND = "firejail"

# Reason code -> failure text. The unsupported text gets the configured value appended by the
# caller; the missing-binary text already names it. Neither ever names a command-allowlist entry.
_SANDBOX_BACKEND_MESSAGES: dict[str, str] = {
    REASON_SANDBOX_BACKEND_UNSUPPORTED: "configured shell sandbox backend is not a sandboxing backend",
    REASON_SANDBOX_BACKEND_MISSING: (
        "shell_sandbox_backend=firejail is configured but firejail is not found in PATH"
    ),
}


def _sandbox_backend_error(backend: str) -> str | None:
    """Return the reason code for a backend Shell cannot prove safe, or None when it is safe.

    The reason code is the classification: callers never parse the message to decide
    which rule failed.
    """
    if backend != _SANDBOX_BACKEND:
        return REASON_SANDBOX_BACKEND_UNSUPPORTED
    if shutil.which(_SANDBOX_BACKEND) is None:
        return REASON_SANDBOX_BACKEND_MISSING
    return None


def _sandbox_backend_message(backend: str, reason_code: str) -> str:
    """Failure text naming the configured backend value only."""
    if reason_code == REASON_SANDBOX_BACKEND_MISSING:
        return _SANDBOX_BACKEND_MESSAGES[reason_code]
    return f"{_SANDBOX_BACKEND_MESSAGES[reason_code]} (backend={backend!r})"


def _resource_limits_error() -> str | None:
    """Return the name of a non-positive resource-limit constant, or None when all are positive.

    The constants are read at call time so the check reflects exactly the limits
    set_resource_limits() is about to apply.
    """
    limits = {
        "_CPU_LIMIT_SAFETY_MULTIPLIER": _CPU_LIMIT_SAFETY_MULTIPLIER,
        "_MIN_CPU_LIMIT_SEC": _MIN_CPU_LIMIT_SEC,
        "_MAX_OPEN_FILE_DESCRIPTORS": _MAX_OPEN_FILE_DESCRIPTORS,
        "_MAX_SUBPROCESS_COUNT": _MAX_SUBPROCESS_COUNT,
        "_MAX_WRITTEN_FILE_MB": _MAX_WRITTEN_FILE_MB,
    }
    for name, value in limits.items():
        if value <= 0:
            return name
    return None


def _check(
    check_id: str,
    status: SecurityCheckStatus,
    reason_code: str,
    message: str,
) -> SecurityCheckResult:
    """One posture check result carrying the shared default versions."""
    return SecurityCheckResult(
        check_id=check_id,
        status=status,
        reason_code=reason_code,
        message=message,
    )


def init_sandbox(backend: str) -> str:
    """Return the backend name when it sandboxes and its binary is present.

    Raises:
        RuntimeError: the backend is "none", empty, unrecognized, or firejail whose binary
            is missing. No backend value is returned without being proven safe.
    """
    reason_code = _sandbox_backend_error(backend)
    if reason_code is not None:
        raise RuntimeError(_sandbox_backend_message(backend, reason_code))
    return backend


def validate_shell_security(
    backend: str,
    command_allowlist: Sequence[str],
) -> list[SecurityCheckResult]:
    """Shell's own security checks, in the fixed order the posture contract expects.

    Never raises for a policy violation: every rule becomes a SecurityCheckResult so the
    failure is reportable in the posture instead of only in an exception message. Messages
    carry the backend name and allowlist length, never allowlist entries.
    """
    reason_code = _sandbox_backend_error(backend)
    backend_supported = reason_code != REASON_SANDBOX_BACKEND_UNSUPPORTED
    limits_error = _resource_limits_error()

    results: list[SecurityCheckResult] = [
        _check(
            "server.sandbox_backend",
            SecurityCheckStatus.OK if backend_supported else SecurityCheckStatus.FAILED,
            REASON_OK if backend_supported else REASON_SANDBOX_BACKEND_UNSUPPORTED,
            "sandbox backend is firejail"
            if backend_supported
            else _sandbox_backend_message(backend, REASON_SANDBOX_BACKEND_UNSUPPORTED),
        ),
        _sandbox_binary_check(backend, reason_code),
        _check(
            "server.command_allowlist",
            SecurityCheckStatus.OK if command_allowlist else SecurityCheckStatus.FAILED,
            REASON_OK if command_allowlist else REASON_ALLOWLIST_EMPTY,
            f"command allowlist has {len(command_allowlist)} entries"
            if command_allowlist
            else "command allowlist is empty",
        ),
        _check(
            "server.resource_limits",
            SecurityCheckStatus.OK
            if limits_error is None
            else SecurityCheckStatus.FAILED,
            REASON_OK if limits_error is None else REASON_CONFIG_INVALID,
            "resource limit constants are positive"
            if limits_error is None
            else f"resource limit constant is not positive: {limits_error}",
        ),
    ]
    return results


def _sandbox_binary_check(backend: str, reason_code: str | None) -> SecurityCheckResult:
    """server.sandbox_binary: the backend's binary is present, or not applicable."""
    if reason_code == REASON_SANDBOX_BACKEND_UNSUPPORTED:
        return _check(
            "server.sandbox_binary",
            SecurityCheckStatus.NOT_APPLICABLE,
            REASON_NOT_APPLICABLE,
            "no sandbox binary to check for an unsupported backend",
        )
    missing = reason_code == REASON_SANDBOX_BACKEND_MISSING
    return _check(
        "server.sandbox_binary",
        SecurityCheckStatus.FAILED if missing else SecurityCheckStatus.OK,
        REASON_SANDBOX_BACKEND_MISSING if missing else REASON_OK,
        _sandbox_backend_message(backend, REASON_SANDBOX_BACKEND_MISSING)
        if missing
        else "firejail binary is present",
    )


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


def is_secret_env_key(key: str) -> bool:
    """Return True when an environment variable name looks like a credential.

    Matches MCP_* names and names with a TOKEN, SECRET, PASSWORD, PASSWD, CREDENTIAL(S) or
    API_KEY word segment; the name is split on underscores so harmless names that merely
    contain such letters (TOKENIZERS_PARALLELISM) are kept.
    """
    segments = key.upper().split("_")
    if segments[0] == "MCP":
        return True
    if any(segment in _SECRET_ENV_SEGMENTS for segment in segments):
        return True
    return any(
        first == "API" and second == "KEY"
        for first, second in zip(segments, segments[1:], strict=False)
    )


def build_command_env(
    base_env: Mapping[str, str], path: str, req_env: Mapping[str, str]
) -> dict[str, str]:
    """Build the environment of a sandboxed command from an explicit allowlist.

    Copies only the base keys from `base_env`, sets PATH, merges the already filtered
    caller `req_env` (which may still override PATH, as before), then drops every
    secret-shaped key so neither the server environment nor `req_env` can pass a
    credential to the command.
    """
    env = {
        key: value
        for key, value in base_env.items()
        if key in _BASE_ENV_KEYS or key.startswith(_BASE_ENV_PREFIXES)
    }
    env["PATH"] = path
    env.update(req_env)
    return {key: value for key, value in env.items() if not is_secret_env_key(key)}
