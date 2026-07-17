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
    FileSecurityMixin,
    check_size_limit,
)


class ReadSecurityGuards(FileSecurityMixin):
    """Mixin that provides path validation and security checks for read operations."""

    def __init__(
        self,
        allowed_dirs: list[Path],
        max_read_bytes: int,
    ) -> None:
        """Initialize the read security guards with allowed directories and byte limit."""
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

    # ── Read-specific security helper ──

    def _check_size_limit(self, target: Path) -> int:
        """Validate that target file does not exceed the configured maximum read size; returns file size."""
        size: int = check_size_limit(target, self._max_read_bytes)
        return size

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
