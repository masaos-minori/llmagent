#!/usr/bin/env python3
"""scripts/mcp_servers/file/common.py

Shared security helpers for file-read-mcp, file-write-mcp, and file-delete-mcp — all functions
raise domain exceptions on policy violations.

validate_file_security_base() is the startup-time entry point: it reports the allowed-directory
rules the three file servers share as Security Posture checks, so each file server validates its
own configuration before HTTP bind instead of being audited by the Agent.
"""

from __future__ import annotations

import os
import stat as _stat
from collections.abc import Sequence
from pathlib import Path

from fastapi import Request
from fastapi.responses import JSONResponse
from shared.security.posture_contract import SecurityPosture
from shared.security.result_dto import (
    REASON_ALLOWED_DIR_INVALID,
    REASON_ALLOWLIST_EMPTY,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)

from mcp_servers.health_response import make_health_response


class FileAuthorizationError(RuntimeError):
    """Raised when a path/permission policy check fails (HTTP 403)."""


class FileValidationError(ValueError):
    """Raised on invalid input (HTTP 400/422)."""


def resolve_safe(raw_path: str, allowed_dirs: list[Path]) -> Path:
    """Resolve symlinks; verify path is under one of allowed_dirs. Raises 403/400."""
    try:
        resolved = Path(raw_path).resolve()
    except OSError as e:
        raise FileValidationError("Invalid path") from e
    for allowed in allowed_dirs:
        try:
            resolved.relative_to(allowed.resolve())
            return resolved
        except ValueError:
            continue
    raise FileAuthorizationError(
        "Access denied: path is outside allowed directories",
    )


def require_file(target: Path, raw_path: str) -> None:
    """Raise 404/400 if target does not exist or is not a file."""
    if not target.exists():
        raise FileNotFoundError(f"File does not exist: {raw_path}")
    if not target.is_file():
        raise FileValidationError(f"Not a file: {raw_path}")


def require_dir(target: Path, raw_path: str) -> None:
    """Raise 404/400 if target does not exist or is not a directory."""
    if not target.exists():
        raise FileNotFoundError(f"Path does not exist: {raw_path}")
    if not target.is_dir():
        raise FileValidationError(f"Not a directory: {raw_path}")


class FileSecurityMixin:
    """Mixin providing path validation methods for file service classes.

    Subclasses must define `self._allowed_dirs: list[Path]`.
    """

    _allowed_dirs: list[Path]

    def _resolve_safe(self, raw_path: str) -> Path:
        """Resolve and validate path against allowed_dirs."""
        resolved: Path = resolve_safe(raw_path, self._allowed_dirs)
        return resolved

    def _require_file(self, target: Path, raw_path: str) -> None:
        """Validate that target is an existing file; raises FileValidationError otherwise."""
        require_file(target, raw_path)

    def _require_dir(self, target: Path, raw_path: str) -> None:
        """Validate that target is an existing directory; raises FileValidationError otherwise."""
        require_dir(target, raw_path)


def check_size_limit(target: Path, max_bytes: int) -> int:
    """Return file size; raise 413 if it exceeds max_bytes."""
    try:
        size = target.stat().st_size
    except OSError as e:
        raise FileValidationError(str(e)) from e
    if size > max_bytes:
        raise FileValidationError(
            f"File size exceeds the limit ({max_bytes} bytes): {size} bytes",
        )
    return size


def format_permissions(mode: int) -> str:
    """Return a 9-char rwx string from a stat mode int."""
    return _stat.filemode(mode)[1:]


def availability_flags(allowed_dirs: list[str]) -> tuple[bool, str]:
    """Return (enabled, disabled_reason) for a file-{read,write,delete} server."""
    if allowed_dirs:
        return True, ""
    return False, "allowed_dirs is empty"


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


def validate_file_security_base(
    allowed_dirs: Sequence[str],
) -> list[SecurityCheckResult]:
    """The allowed-directories checks every file server shares, in the fixed order.

    Startup-time view of the same facts availability_flags() and _build_health_deps() report at
    request time: an empty allowlist means the server is disabled, and a configured entry that is
    not a directory means the server cannot operate on it. It never raises for a policy violation,
    and the two check ids are always present, with not_applicable used instead of omitting a check.

    Existence is tested on the configured string with Path.is_dir(); symlink resolution stays a
    request-time concern already handled by resolve_safe(). An empty entry counts as invalid
    because it resolves to the current working directory, which is not a configured boundary.

    Messages report counts and state only: allowed directory paths are sensitive paths.
    """
    if allowed_dirs:
        configured_check = _check(
            "server.allowed_dirs_configured",
            SecurityCheckStatus.OK,
            REASON_OK,
            "configured allowed_dirs is non-empty",
        )
    else:
        configured_check = _check(
            "server.allowed_dirs_configured",
            SecurityCheckStatus.FAILED,
            REASON_ALLOWLIST_EMPTY,
            "allowed_dirs is empty so the server is disabled",
        )

    invalid = [entry for entry in allowed_dirs if not entry or not Path(entry).is_dir()]
    if not allowed_dirs:
        exist_check = _check(
            "server.allowed_dirs_exist",
            SecurityCheckStatus.NOT_APPLICABLE,
            REASON_NOT_APPLICABLE,
            "no allowed_dirs entry is configured to check",
        )
    elif invalid:
        exist_check = _check(
            "server.allowed_dirs_exist",
            SecurityCheckStatus.FAILED,
            REASON_ALLOWED_DIR_INVALID,
            f"{len(invalid)} of {len(allowed_dirs)} allowed_dirs entries are not directories",
        )
    else:
        exist_check = _check(
            "server.allowed_dirs_exist",
            SecurityCheckStatus.OK,
            REASON_OK,
            "every allowed_dirs entry is an existing directory",
        )

    return [configured_check, exist_check]


def _build_health_deps(allowed_dirs: list[str]) -> dict[str, str]:
    """Build health check dependency status dict.

    Checks that the server's own configured allowed_dirs exist, since those
    are the only directories the server can actually operate on.
    Returns an empty dict when all dependencies are healthy,
    or a dict with error messages for failed checks.
    """
    deps: dict[str, str] = {}
    for raw_dir in allowed_dirs:
        try:
            if not _stat.S_ISDIR(os.stat(raw_dir).st_mode):
                deps["filesystem"] = f"{raw_dir} is not a directory"
                break
        except OSError as e:
            deps["filesystem"] = f"check failed: {e}"
            break
    return deps


# ── Common exception handlers and health endpoint ─────────────────────────────


def _make_error_handler(status_code: int):
    async def handler(_req: Request, exc: Exception) -> JSONResponse:
        return JSONResponse({"detail": str(exc)}, status_code=status_code)

    return handler


_on_auth_error = _make_error_handler(403)
_on_not_found = _make_error_handler(404)
_on_validation_error = _make_error_handler(422)


async def _health(
    allowed_dirs: list[str],
    posture: SecurityPosture | None = None,
) -> JSONResponse:
    """Build and return a health check response, publishing this server's posture when given.

    deps stays the availability view and details stays empty: posture data is not folded into
    details. ready is derived by make_health_response() so the three file servers cannot each
    invent their own rule. The posture parameter is optional so a file server that has not been
    wired yet keeps publishing today's payload unchanged.
    """
    deps = _build_health_deps(allowed_dirs)
    return make_health_response(deps, {}, security=posture)
