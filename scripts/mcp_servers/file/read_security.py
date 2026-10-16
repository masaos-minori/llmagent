#!/usr/bin/env python3
"""scripts/mcp_servers/file/read_security.py

ReadSecurityGuards mixin for read-only filesystem operations — path validation and size limits.

Extracted from read_business.py to reduce file size.

validate_file_read_security() is the startup-time entry point: it reports this server's own
configuration as a Security Posture, so file-read-mcp validates itself before HTTP bind instead of
being audited by the Agent.

Dependency direction: read_security → common
Import from here:  from mcp_servers.file.read_security import ReadSecurityGuards
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from shared.security.result_dto import (
    REASON_CONFIG_INVALID,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)

from mcp_servers.file.common import (
    FileSecurityMixin,
    check_size_limit,
    validate_file_security_base,
)
from mcp_servers.file.read_models import FileReadConfig


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
        expected_type: Literal["file", "dir"] = "file",
    ) -> tuple[Path, int]:
        """Resolve path, require it's a file/directory, check size limit. Return (target, size)."""
        target = self._resolve_safe(raw_path)
        if expected_type == "file":
            self._require_file(target, raw_path)
            size = self._check_size_limit(target)
        else:
            self._require_dir(target, raw_path)
            size = 0
        return target, size


def validate_file_read_security(cfg: FileReadConfig) -> list[SecurityCheckResult]:
    """File-read's own configuration checks: the shared allowed-dirs base plus the byte limit.

    The shared part is delegated to validate_file_security_base() so one definition of the
    allowed-dirs rules serves all three file servers. The function is pure: it stats configured
    directories but never creates, writes, or deletes anything, and it never raises for a policy
    violation.

    A non-positive max_read_bytes is a configuration error rather than a policy choice:
    check_size_limit() would then reject every read while the server still advertises itself.

    Messages report counts and setting names only: allowed directory paths are sensitive paths.
    """
    checks = validate_file_security_base(cfg.allowed_dirs)
    if cfg.max_read_bytes > 0:
        limit_status = SecurityCheckStatus.OK
        limit_reason = REASON_OK
        limit_message = "configured max_read_bytes is positive"
    else:
        limit_status = SecurityCheckStatus.FAILED
        limit_reason = REASON_CONFIG_INVALID
        limit_message = "max_read_bytes is not positive so every read is rejected"
    checks.append(
        SecurityCheckResult(
            check_id="server.max_read_bytes",
            status=limit_status,
            reason_code=limit_reason,
            message=limit_message,
        )
    )
    return checks
