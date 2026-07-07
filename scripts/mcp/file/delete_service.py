#!/usr/bin/env python3
"""file_delete_mcp_service.py
DeleteFileService business logic, audit log, and lazy singleton proxy for file-delete-mcp.

Dependency direction: file_delete_mcp_models → file_delete_mcp_service → file_delete_mcp_server
"""

from __future__ import annotations

import asyncio
import logging
import os
import shutil
import stat as stat_module
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime
from pathlib import Path

from mcp.file.common import (
    FileAuthorizationError,
    FileValidationError,
    require_dir,
    require_file,
    resolve_safe,
)
from mcp.file.delete_formatter import DeleteFileFormatter
from mcp.file.delete_models import (
    DeleteDirectoryRequest,
    DeleteDirectoryResponse,
    DeleteFileRequest,
    DeleteFileResponse,
    FileDeleteConfig,
)
from mcp.server import ToolArgs

# Standard library logger; log path is owned by file_delete_mcp_server.py
logger = logging.getLogger(__name__)

# Upper bound on files scanned during delete_directory dry_run to avoid hanging
_DRY_RUN_MAX_FILES = 1000


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
            logger.error("_write_audit_log: failed to write audit log: %s", e)

    # ── Business operation methods ──

    def delete_file(self, req: DeleteFileRequest) -> DeleteFileResponse:
        """Delete the specified file and record the operation in the audit log."""
        target = self._resolve_safe(req.path)
        self._require_file(target, req.path)
        if req.dry_run:
            try:
                st = target.stat()
                mode = oct(stat_module.S_IMODE(st.st_mode))
                mtime = datetime.fromtimestamp(st.st_mtime, tz=UTC).isoformat()
                file_info = f"size={st.st_size}, mode={mode}, mtime={mtime}"
            except OSError as e:
                file_info = f"stat error: {e}"
            return DeleteFileResponse(
                path=str(target),
                deleted=False,
                file_info=file_info,
            )
        try:
            target.unlink()
        except PermissionError as e:
            raise FileAuthorizationError(str(e))
        except OSError as e:
            logger.error("delete_file: OS error deleting '%s': %s", target, e)
            raise FileValidationError(str(e))

        # Audit log written after successful deletion
        self._write_audit_log("delete_file", str(target))
        return DeleteFileResponse(path=str(target), deleted=True, file_info="")

    def _scan_directory_for_dry_run(self, target: Path) -> tuple[int, int, bool]:
        """Walk target and return (file_count, total_size_bytes, truncated).

        Stops counting after _DRY_RUN_MAX_FILES files to avoid blocking on huge trees.
        OSError on individual files are skipped; OSError on the walk itself propagates.
        """
        file_count = 0
        total_size = 0
        for dirpath, _, filenames in os.walk(str(target)):
            for fname in filenames:
                if file_count >= _DRY_RUN_MAX_FILES:
                    return file_count, total_size, True
                try:
                    fpath = Path(dirpath) / fname
                    total_size += fpath.stat().st_size
                    file_count += 1
                except OSError:
                    continue
        return file_count, total_size, False

    def delete_directory(self, req: DeleteDirectoryRequest) -> DeleteDirectoryResponse:
        """Delete a directory and record the operation in the audit log.

        Raises if not empty when recursive=False.
        """
        target = self._resolve_safe(req.path)
        self._require_dir(target, req.path)

        if req.dry_run:
            try:
                file_count, total_size, truncated = self._scan_directory_for_dry_run(
                    target,
                )
            except OSError as e:
                return DeleteDirectoryResponse(
                    path=str(target),
                    deleted=False,
                    dir_info=f"scan error: {e}",
                )
            count_str = f"{file_count}+" if truncated else str(file_count)
            return DeleteDirectoryResponse(
                path=str(target),
                deleted=False,
                dir_info=f"{count_str} files, {total_size} bytes",
            )

        if req.recursive:
            for allowed in self._allowed_dirs:
                if target == allowed.resolve():
                    raise FileAuthorizationError(
                        f"Deleting an allowed root directory is not permitted: {target}",
                    )

        try:
            if req.recursive:
                shutil.rmtree(str(target))
            else:
                # Raises OSError (errno 39 ENOTEMPTY) if the directory is not empty
                target.rmdir()
        except PermissionError as e:
            # PermissionError is a subclass of OSError, so catch it first
            raise FileAuthorizationError(str(e))
        except OSError as e:
            raise FileValidationError(str(e))

        # Audit log written after successful deletion
        self._write_audit_log("delete_directory", str(target))
        return DeleteDirectoryResponse(path=str(target), deleted=True, dir_info="")

    # ── Dispatch handlers: format service results as plain text for the LLM ──

    async def fmt_delete_file(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            lambda: self.delete_file(DeleteFileRequest(**args)),
        )
        return DeleteFileFormatter.format_file_result(result)

    async def fmt_delete_directory(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            lambda: self.delete_directory(DeleteDirectoryRequest(**args)),
        )
        return DeleteFileFormatter.format_directory_result(result)

    def get_dispatch_table(
        self,
    ) -> dict[str, Callable[[ToolArgs], Awaitable[str]]]:
        """Build and return the MCP tool dispatch table keyed by tool name."""
        return {
            "delete_file": self.fmt_delete_file,
            "delete_directory": self.fmt_delete_directory,
        }


def build_service(cfg: FileDeleteConfig) -> DeleteFileService:
    """Construct a DeleteFileService from a typed config object."""
    allowed_dirs = [Path(d) for d in cfg.allowed_dirs]
    if not allowed_dirs:
        logger.warning("ALLOWED_DIRS is empty — all paths will be rejected")
    return DeleteFileService(
        allowed_dirs=allowed_dirs,
        audit_log_path="/opt/llm/logs/delete_audit.log",
    )
