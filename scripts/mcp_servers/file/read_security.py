#!/usr/bin/env python3
"""mcp_servers/file/read_security.py
ReadSecurityGuards mixin for read-only filesystem operations.

Extracted from read_business.py to reduce file size.

Dependency direction: read_security → common
Import from here:  from mcp_servers.file.read_security import ReadSecurityGuards
"""

from __future__ import annotations

from pathlib import Path

from mcp_servers.file.common import (
    check_size_limit,
    require_dir,
    require_file,
    resolve_safe,
)


class ReadSecurityGuards:
    """Mixin that provides path validation and security checks for read operations."""

    def __init__(
        self,
        allowed_dirs: list[Path],
        max_read_bytes: int,
    ) -> None:
        self._allowed_dirs = allowed_dirs
        self._max_read_bytes = max_read_bytes

    @property
    def allowed_dirs(self) -> list[Path]:
        """Allowed directories for read operations."""
        return self._allowed_dirs

    @property
    def max_read_bytes(self) -> int:
        """Maximum read size configured for this service."""
        return self._max_read_bytes

    # ── Security wrappers (delegate to file_mcp_common) ──

    def _resolve_safe(self, raw_path: str) -> Path:
        """Resolve and validate path against allowed_dirs."""
        return resolve_safe(raw_path, self._allowed_dirs)

    def _require_file(self, target: Path, raw_path: str) -> None:
        require_file(target, raw_path)

    def _require_dir(self, target: Path, raw_path: str) -> None:
        require_dir(target, raw_path)

    def _check_size_limit(self, target: Path) -> int:
        return check_size_limit(target, self._max_read_bytes)

    # ── Shared validation pipeline for file read operations ──

    def _validate_file(
        self,
        raw_path: str,
        *,
        expected_type: str = "file",
    ) -> tuple[Path, int]:
        """Resolve path, require it's a file/directory, check size limit. Return (target, size)."""
        target = self._resolve_safe(raw_path)
        if expected_type == "file":
            self._require_file(target, raw_path)
        else:
            self._require_dir(target, raw_path)
        size = self._check_size_limit(target)
        return target, size
