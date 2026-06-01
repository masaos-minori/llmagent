#!/usr/bin/env python3
"""file_mcp_common.py
Shared security helpers for file-read-mcp, file-write-mcp, and file-delete-mcp.
All functions raise FastAPI HTTPException on policy violations.
"""

from __future__ import annotations

import stat as _stat
from pathlib import Path

from fastapi import HTTPException


def resolve_safe(raw_path: str, allowed_dirs: list[Path]) -> Path:
    """Resolve symlinks; verify path is under one of allowed_dirs. Raises 403/400."""
    try:
        resolved = Path(raw_path).resolve()
    except OSError:
        raise HTTPException(status_code=400, detail="Invalid path")
    for allowed in allowed_dirs:
        try:
            resolved.relative_to(allowed.resolve())
            return resolved
        except ValueError:
            continue
    raise HTTPException(
        status_code=403,
        detail="Access denied: path is outside allowed directories",
    )


def require_file(target: Path, raw_path: str) -> None:
    """Raise 404/400 if target does not exist or is not a file."""
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"File does not exist: {raw_path}")
    if not target.is_file():
        raise HTTPException(status_code=400, detail=f"Not a file: {raw_path}")


def require_dir(target: Path, raw_path: str) -> None:
    """Raise 404/400 if target does not exist or is not a directory."""
    if not target.exists():
        raise HTTPException(status_code=404, detail=f"Path does not exist: {raw_path}")
    if not target.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a directory: {raw_path}")


def check_size_limit(target: Path, max_bytes: int) -> int:
    """Return file size; raise 413 if it exceeds max_bytes."""
    try:
        size = target.stat().st_size
    except OSError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if size > max_bytes:
        raise HTTPException(
            status_code=413,
            detail=f"File size exceeds the limit ({max_bytes} bytes): {size} bytes",
        )
    return size


def format_permissions(mode: int) -> str:
    """Return a 9-char rwx string from a stat mode int."""
    return _stat.filemode(mode)[1:]
