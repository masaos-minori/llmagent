#!/usr/bin/env python3
"""scripts/mcp_servers/file/delete_service.py

DeleteFileService business logic, audit log, and lazy singleton proxy for file-delete-mcp — every
path policy violation raises a domain exception.

validate_file_delete_security() is the startup-time entry point: it reports this server's own
configuration and its audit-log dependency as a Security Posture, so file-delete-mcp validates
itself before HTTP bind instead of being audited by the Agent.

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

from shared.json_utils import now_iso_raw
from shared.security.result_dto import (
    REASON_CONFIG_INVALID,
    REASON_DEPENDENCY_UNREACHABLE,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)

from mcp_servers.file.common import (
    FileAuthorizationError,
    FileSecurityMixin,
    FileValidationError,
    validate_file_security_base,
)
from mcp_servers.file.delete_formatter import DeleteFileFormatter
from mcp_servers.file.delete_models import (
    DeleteDirectoryRequest,
    DeleteDirectoryResponse,
    DeleteFileRequest,
    DeleteFileResponse,
    FileDeleteConfig,
)
from mcp_servers.server import ToolArgs

# Standard library logger; log path is owned by file_delete_mcp_server.py
logger = logging.getLogger(__name__)

# Upper bound on files scanned during delete_directory dry_run to avoid hanging
_DRY_RUN_MAX_FILES = 1000

# Audit log destination. Not configuration: config/file_delete_mcp_server.toml records that
# audit_log_path was removed from the config layer. A deployment path, not a Secret.
AUDIT_LOG_PATH = "/opt/llm/logs/delete_audit.log"


class DeleteFileService(FileSecurityMixin):
    """Encapsulates delete filesystem operations with security boundaries and audit logging."""

    def __init__(
        self,
        allowed_dirs: list[Path],
        audit_log_path: str,
    ) -> None:
        """Initialize the delete file service with allowed directories and audit log path."""
        self._allowed_dirs = allowed_dirs
        self._audit_log_path = audit_log_path

    # ── Audit log ──

    def _write_audit_log(self, op: str, path: str) -> None:
        """Append a single audit record to the audit log file.

        Format: {ISO8601} op={op} path={path} user=llm-agent
        Writing errors are logged but never propagated — audit failure must not
        block the actual delete operation from returning a result to the caller.
        """
        ts = now_iso_raw()
        record = f"{ts} op={op} path={path} user=llm-agent\n"
        try:
            with open(self._audit_log_path, "a", encoding="utf-8") as fh:
                fh.write(record)
        except OSError as e:
            logger.error("_write_audit_log: failed to write audit log: %s", e)

    # ── Business operation methods ──

    def _stat_info_for_dry_run(self, target: Path) -> str:
        """Return a human-readable size/mode/mtime string, or a "stat error: ..." string."""
        try:
            st = target.stat()
            mode = oct(stat_module.S_IMODE(st.st_mode))
            mtime = datetime.fromtimestamp(st.st_mtime, tz=UTC).isoformat()
            return f"size={st.st_size}, mode={mode}, mtime={mtime}"
        except OSError as e:
            return f"stat error: {e}"

    def delete_file(self, req: DeleteFileRequest) -> DeleteFileResponse:
        """Delete the specified file and record the operation in the audit log."""
        target = self._resolve_safe(req.path)
        self._require_file(target, req.path)
        if req.dry_run:
            return DeleteFileResponse(
                path=str(target),
                deleted=False,
                file_info=self._stat_info_for_dry_run(target),
            )
        try:
            target.unlink()
        except PermissionError as e:
            raise FileAuthorizationError(str(e))
        except OSError as e:
            logger.error("delete_file: OS error deleting '%s': %s", target, e)
            raise FileValidationError(str(e))

        self._verify_deleted(target)

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

    def _dry_run_directory_response(self, target: Path) -> DeleteDirectoryResponse:
        """Build the dry-run response describing directory contents, without deleting."""
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

    @staticmethod
    def _verify_deleted(target: Path) -> None:
        """Raise FileValidationError if the target still exists after deletion."""
        if target.exists():
            raise FileValidationError(
                f"post-delete verification failed: {target} still exists",
            )

    def _check_not_deleting_allowed_root(self, target: Path) -> None:
        """Raise FileAuthorizationError if target is itself one of the allowed root dirs."""
        for allowed in self._allowed_dirs:
            if target == allowed.resolve():
                raise FileAuthorizationError(
                    f"Deleting an allowed root directory is not permitted: {target}",
                )

    def delete_directory(self, req: DeleteDirectoryRequest) -> DeleteDirectoryResponse:
        """Delete a directory and record the operation in the audit log.

        Raises if not empty when recursive=False.
        """
        target = self._resolve_safe(req.path)
        self._require_dir(target, req.path)

        if req.dry_run:
            return self._dry_run_directory_response(target)

        self._check_not_deleting_allowed_root(target)

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

        self._verify_deleted(target)

        # Audit log written after successful deletion
        self._write_audit_log("delete_directory", str(target))
        return DeleteDirectoryResponse(path=str(target), deleted=True, dir_info="")

    # ── Dispatch handlers: format service results as plain text for the LLM ──

    async def fmt_delete_file(self, args: ToolArgs) -> str:
        """Delete a single file and format the result as plain text."""
        result = await asyncio.to_thread(
            lambda: self.delete_file(
                DeleteFileRequest(
                    path=args["path"],
                    dry_run=args.get("dry_run", False),
                )
            ),
        )
        formatted: str = DeleteFileFormatter.format_file_result(result)
        return formatted

    async def fmt_delete_directory(self, args: ToolArgs) -> str:
        """Delete a directory recursively and format the result as plain text."""
        result = await asyncio.to_thread(
            lambda: self.delete_directory(
                DeleteDirectoryRequest(
                    path=args["path"],
                    recursive=args.get("recursive", False),
                    dry_run=args.get("dry_run", False),
                )
            ),
        )
        formatted: str = DeleteFileFormatter.format_directory_result(result)
        return formatted

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
        audit_log_path=AUDIT_LOG_PATH,
    )


def validate_file_delete_security(
    cfg: FileDeleteConfig,
    audit_log_path: str = AUDIT_LOG_PATH,
) -> list[SecurityCheckResult]:
    """File-delete's own configuration checks, in the order the posture contract expects.

    The allowed-directories part is delegated to validate_file_security_base() so one definition of
    those rules serves all three file servers. The function never raises for a policy violation and
    performs no filesystem mutation: audit-log writability is tested with os.access on the parent
    directory instead of by appending a probe record.

    An audit log that cannot be written is FAILED, not a warning. Delete is the one file server
    whose destructive operations are recorded, so a server that cannot record them must not start;
    this matches the same dependency reported FAILED by github-mcp (row `09`).

    Messages report counts and setting names only: allowed directory paths and the audit log path
    are sensitive values.
    """
    checks = validate_file_security_base(cfg.allowed_dirs)

    roots = [
        entry
        for entry in cfg.allowed_dirs
        if entry and Path(entry).resolve() == Path("/")
    ]
    if not cfg.allowed_dirs:
        root_status = SecurityCheckStatus.NOT_APPLICABLE
        root_reason = REASON_NOT_APPLICABLE
        root_message = "no allowed_dirs entry is configured to allow a delete"
    elif roots:
        root_status = SecurityCheckStatus.FAILED
        root_reason = REASON_CONFIG_INVALID
        root_message = (
            f"allowed_dirs contains the filesystem root in {len(roots)} of "
            f"{len(cfg.allowed_dirs)} entries"
        )
    else:
        root_status = SecurityCheckStatus.OK
        root_reason = REASON_OK
        root_message = "no allowed_dirs entry resolves to the filesystem root"
    checks.append(
        SecurityCheckResult(
            check_id="server.allowed_root_protected",
            status=root_status,
            reason_code=root_reason,
            message=root_message,
        )
    )

    if not audit_log_path:
        audit_status = SecurityCheckStatus.NOT_APPLICABLE
        audit_reason = REASON_NOT_APPLICABLE
        audit_message = "audit_log_path is empty so audit records are not written"
    elif Path(audit_log_path).is_dir():
        audit_status = SecurityCheckStatus.FAILED
        audit_reason = REASON_DEPENDENCY_UNREACHABLE
        audit_message = (
            "audit log path is an existing directory so no audit file can be written"
        )
    elif not Path(audit_log_path).parent.is_dir():
        audit_status = SecurityCheckStatus.FAILED
        audit_reason = REASON_DEPENDENCY_UNREACHABLE
        audit_message = "audit log parent directory does not exist"
    elif not os.access(Path(audit_log_path).parent, os.W_OK):
        audit_status = SecurityCheckStatus.FAILED
        audit_reason = REASON_DEPENDENCY_UNREACHABLE
        audit_message = "audit log parent directory is not writable"
    else:
        audit_status = SecurityCheckStatus.OK
        audit_reason = REASON_OK
        audit_message = "configured audit log path has a writable parent directory"
    checks.append(
        SecurityCheckResult(
            check_id="server.audit_log_writable",
            status=audit_status,
            reason_code=audit_reason,
            message=audit_message,
        )
    )
    return checks
