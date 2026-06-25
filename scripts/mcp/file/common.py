#!/usr/bin/env python3
"""file_mcp_common.py
Shared security helpers for file-read-mcp, file-write-mcp, and file-delete-mcp.
All functions raise domain exceptions on policy violations.
"""

from __future__ import annotations

import os
import stat as _stat
from pathlib import Path


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


def _build_health_deps() -> dict[str, str]:
    """Build health check dependency status dict.

    Returns an empty dict when all dependencies are healthy,
    or a dict with error messages for failed checks.
    """
    deps: dict[str, str] = {}
    try:
        if not _stat.S_ISDIR(os.stat("/workspace").st_mode):
            deps["filesystem"] = "/workspace is not a directory"
    except OSError as e:
        deps["filesystem"] = f"check failed: {e}"
    return deps
