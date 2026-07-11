#!/usr/bin/env python3
"""file_mcp_common.py
Shared security helpers for file-read-mcp, file-write-mcp, and file-delete-mcp.
All functions raise domain exceptions on policy violations.
"""

from __future__ import annotations

import os
import stat as _stat
from pathlib import Path

from fastapi import Request
from fastapi.responses import JSONResponse


class FileAuthorizationError(RuntimeError):
    """Raised when a path/permission policy check fails (HTTP 403)."""


class FileValidationError(ValueError):
    """Raised on invalid input (HTTP 400/422)."""


def resolve_safe(raw_path: str, allowed_dirs: list[Path]) -> Path:
    """Resolve symlinks; verify path is under one of allowed_dirs. Raises 403/400."""
    try:
        resolved = Path(raw_path).resolve()
    except OSError:
        raise FileValidationError("Invalid path")
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


def check_size_limit(target: Path, max_bytes: int) -> int:
    """Return file size; raise 413 if it exceeds max_bytes."""
    try:
        size = target.stat().st_size
    except OSError as e:
        raise FileValidationError(str(e))
    if size > max_bytes:
        raise FileValidationError(
            f"File size exceeds the limit ({max_bytes} bytes): {size} bytes",
        )
    return size


def format_permissions(mode: int) -> str:
    """Return a 9-char rwx string from a stat mode int."""
    return _stat.filemode(mode)[1:]


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


async def _on_auth_error(_req: Request, exc: Exception) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=403)


async def _on_not_found(_req: Request, exc: Exception) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=404)


async def _on_validation_error(_req: Request, exc: Exception) -> JSONResponse:
    return JSONResponse({"detail": str(exc)}, status_code=422)


async def _health(allowed_dirs: list[str]) -> JSONResponse:
    deps = _build_health_deps(allowed_dirs)
    ready = len(deps) == 0
    return JSONResponse(
        {
            "status": "ok" if ready else "degraded",
            "ready": ready,
            "liveness": True,
            "restart_recommended": False,
            "operator_action_required": not ready,
            "dependencies": deps,
            "details": {},
        },
        status_code=200 if ready else 503,
    )
