#!/usr/bin/env python3
"""
file_delete_mcp_service.py
DeleteFileService business logic, audit log, and lazy singleton proxy for file-delete-mcp.

Dependency direction: file_delete_mcp_models → file_delete_mcp_service → file_delete_mcp_server
"""

from __future__ import annotations

import logging
import shutil
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from file_delete_mcp_models import (
    DeleteDirectoryRequest,
    DeleteDirectoryResponse,
    DeleteFileRequest,
    DeleteFileResponse,
    _get_cfg,
)
from file_mcp_common import require_dir, require_file, resolve_safe
from mcp_server import ToolArgs

# Standard library logger; log path is owned by file_delete_mcp_server.py
logger = logging.getLogger(__name__)


class DeleteFileService:
    """Encapsulates delete filesystem operations with security boundaries and audit logging."""

    def __init__(
        self,
        allowed_dirs: list[Path],
        audit_log_path: str,
    ) -> None:
        self._allowed_dirs = allowed_dirs
        self._audit_log_path = audit_log_path

    # ── Security wrappers (delegate to file_mcp_common) ──

    def _resolve_safe(self, raw_path: str) -> Path:
        """Resolve and validate path against allowed_dirs."""
        return resolve_safe(raw_path, self._allowed_dirs)

    def _require_file(self, target: Path, raw_path: str) -> None:
        require_file(target, raw_path)

    def _require_dir(self, target: Path, raw_path: str) -> None:
        require_dir(target, raw_path)

    # ── Audit log ──

    def _write_audit_log(self, op: str, path: str) -> None:
        """Append a single audit record to the audit log file.

        Format: {ISO8601} op={op} path={path} user=llm-agent
        Writing errors are logged but never propagated — audit failure must not
        block the actual delete operation from returning a result to the caller.
        """
        ts = datetime.now(tz=UTC).isoformat()
        record = f"{ts} op={op} path={path} user=llm-agent\n"
        try:
            with open(self._audit_log_path, "a", encoding="utf-8") as fh:
                fh.write(record)
        except OSError as e:
            logger.error(f"_write_audit_log: failed to write audit log: {e}")

    # ── Business operation methods ──

    def delete_file(self, req: DeleteFileRequest) -> DeleteFileResponse:
        """Delete the specified file and record the operation in the audit log."""
        target = self._resolve_safe(req.path)
        self._require_file(target, req.path)
        try:
            target.unlink()
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except OSError as e:
            logger.error(f"delete_file: OS error deleting '{target}': {e}")
            raise HTTPException(status_code=400, detail=str(e))

        # Audit log written after successful deletion
        self._write_audit_log("delete_file", str(target))
        return DeleteFileResponse(path=str(target), deleted=True)

    def delete_directory(self, req: DeleteDirectoryRequest) -> DeleteDirectoryResponse:
        """Delete a directory and record the operation in the audit log.

        Raises if not empty when recursive=False.
        """
        target = self._resolve_safe(req.path)
        self._require_dir(target, req.path)

        try:
            if req.recursive:
                shutil.rmtree(str(target))
            else:
                # Raises OSError (errno 39 ENOTEMPTY) if the directory is not empty
                target.rmdir()
        except PermissionError as e:
            # PermissionError is a subclass of OSError, so catch it first
            raise HTTPException(status_code=403, detail=str(e))
        except OSError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Audit log written after successful deletion
        self._write_audit_log("delete_directory", str(target))
        return DeleteDirectoryResponse(path=str(target), deleted=True)

    # ── Dispatch handlers: format service results as plain text for the LLM ──

    async def fmt_delete_file(self, args: ToolArgs) -> str:
        result = self.delete_file(DeleteFileRequest(**args))
        return f"Deleted: {result.path}"

    async def fmt_delete_directory(self, args: ToolArgs) -> str:
        result = self.delete_directory(DeleteDirectoryRequest(**args))
        return f"Directory deleted: {result.path}"

    def get_dispatch_table(
        self,
    ) -> dict[str, Callable[[ToolArgs], Awaitable[str]]]:
        """Build and return the MCP tool dispatch table keyed by tool name."""
        return {
            "delete_file": self.fmt_delete_file,
            "delete_directory": self.fmt_delete_directory,
        }


class _LazyDeleteFileService:
    """Lazy singleton proxy: defers DeleteFileService init until first attribute access."""

    _instance: DeleteFileService | None = None

    def __getattr__(self, name: str) -> Any:
        if _LazyDeleteFileService._instance is None:
            cfg = _get_cfg()
            allowed_dirs = [Path(d) for d in cfg.get("allowed_dirs", [])]
            if not allowed_dirs:
                logger.warning("ALLOWED_DIRS is empty — all paths will be rejected")
            _LazyDeleteFileService._instance = DeleteFileService(
                allowed_dirs=allowed_dirs,
                audit_log_path=cfg.get(
                    "audit_log_path", "/opt/llm/logs/delete_audit.log"
                ),
            )
        return getattr(_LazyDeleteFileService._instance, name)


# Singleton proxy; actual DeleteFileService is created on first attribute access
_service: DeleteFileService = _LazyDeleteFileService()  # type: ignore[assignment]
