#!/usr/bin/env python3
"""file_write_mcp_service.py
WriteFileService business logic and lazy singleton proxy for file-write-mcp.

Dependency direction: file_write_mcp_models → file_write_mcp_service → file_write_mcp_server
"""

from __future__ import annotations

import asyncio
import difflib
import logging
import os
import shutil
from collections.abc import Awaitable, Callable
from pathlib import Path

from mcp.file.common import (
    FileAuthorizationError,
    FileValidationError,
    require_file,
    resolve_safe,
)
from mcp.file.write_models import (
    CreateDirectoryRequest,
    CreateDirectoryResponse,
    EditFileRequest,
    EditFileResponse,
    EditOperation,
    FileWriteConfig,
    MoveFileRequest,
    MoveFileResponse,
    WriteFileRequest,
    WriteFileResponse,
)
from mcp.server import ToolArgs

# Standard library logger; log path is owned by mcp/file/write_server.py
logger = logging.getLogger(__name__)


class WriteFileService:
    """Encapsulates write/create/move filesystem operations with security boundaries."""

    def __init__(
        self,
        allowed_dirs: list[Path],
        max_write_bytes: int,
    ) -> None:
        self._allowed_dirs = allowed_dirs
        self._max_write_bytes = max_write_bytes

    # ── Security wrappers (delegate to file_mcp_common) ──

    def _resolve_safe(self, raw_path: str) -> Path:
        """Resolve and validate path against allowed_dirs."""
        return resolve_safe(raw_path, self._allowed_dirs)

    def _require_file(self, target: Path, raw_path: str) -> None:
        require_file(target, raw_path)

    # ── Static helpers ──

    @staticmethod
    def _apply_text_edits(content: str, edits: list[EditOperation]) -> str:
        """Apply each edit in order. Raises FileValidationError if old_text not found."""
        modified = content
        for i, op in enumerate(edits, start=1):
            if op.old_text not in modified:
                raise FileValidationError(
                    (f"Edit {i}: replacement target not found: {op.old_text[:80]!r}"),
                )
            modified = modified.replace(op.old_text, op.new_text, 1)
        return modified

    @staticmethod
    def _generate_diff(
        target: Path,
        original: str,
        modified: str,
    ) -> str:
        """Generate a unified diff between original and modified content."""
        if original == modified:
            return ""
        diff_lines = difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile=f"a/{target.name}",
            tofile=f"b/{target.name}",
        )
        return "".join(diff_lines)

    @staticmethod
    def _write_content(target: Path, content: str) -> None:
        """Write content to target file. Raises FileAuthorizationError on permission error."""
        try:
            target.write_text(content, encoding="utf-8")
        except PermissionError as e:
            raise FileAuthorizationError(str(e))

    @staticmethod
    def _cleanup_tmp(tmp: Path) -> None:
        """Remove tmp file if it exists."""
        try:
            tmp.unlink(missing_ok=True)
        except OSError:
            pass

    @staticmethod
    def _write_if_changed(
        target: Path,
        original: str,
        modified: str,
        dry_run: bool,
    ) -> tuple[str, bool]:
        """Generate a unified diff and write the file if changed and not a dry run.
        Returns (diff_text, applied).
        """
        diff = WriteFileService._generate_diff(target, original, modified)
        applied = False
        if not dry_run and modified != original:
            WriteFileService._write_content(target, modified)
            applied = True
        return diff, applied

    # ── Business operation methods ──

    def write_file(self, req: WriteFileRequest) -> WriteFileResponse:
        """Create or overwrite a file; parent directories created automatically."""
        target = self._resolve_safe(req.path)
        raw_bytes = req.content.encode("utf-8")
        size = len(raw_bytes)
        if size > self._max_write_bytes:
            raise FileValidationError(
                f"content exceeds {self._max_write_bytes} bytes write limit"
            )
        if req.dry_run:
            return self._write_file_dry_run(target, req.content, size)
        tmp = target.parent / f".tmp_{target.name}"
        try:
            target.parent.mkdir(parents=True, exist_ok=True)
            tmp.write_text(req.content, encoding="utf-8")
            os.replace(str(tmp), str(target))
        except PermissionError as e:
            WriteFileService._cleanup_tmp(tmp)
            raise FileAuthorizationError(str(e))
        except OSError as e:
            WriteFileService._cleanup_tmp(tmp)
            logger.error("write_file: OS error writing '%s': %s", target, e)
            raise FileValidationError(str(e))

        size = target.stat().st_size
        return WriteFileResponse(path=str(target), size=size, applied=True, diff="")

    def _write_file_dry_run(
        self,
        target: Path,
        content: str,
        size: int,
    ) -> WriteFileResponse:
        """Return a diff against existing file content without writing."""
        diff = ""
        if target.exists():
            try:
                original = target.read_text(encoding="utf-8")
                diff, _ = WriteFileService._write_if_changed(
                    target,
                    original,
                    content,
                    True,
                )
            except UnicodeDecodeError:
                raise FileValidationError("Existing file cannot be decoded as UTF-8")
            except PermissionError as e:
                raise FileAuthorizationError(str(e))
        return WriteFileResponse(
            path=str(target),
            size=size,
            applied=False,
            diff=diff,
        )

    def edit_file(self, req: EditFileRequest) -> EditFileResponse:
        """Apply string replacements to a file; dry_run returns only the diff."""
        target = self._resolve_safe(req.path)
        self._require_file(target, req.path)
        try:
            original = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise FileValidationError(
                "File cannot be decoded as UTF-8",
            )
        except PermissionError as e:
            raise FileAuthorizationError(str(e))
        modified = WriteFileService._apply_text_edits(original, req.edits)
        diff, applied = WriteFileService._write_if_changed(
            target,
            original,
            modified,
            req.dry_run,
        )
        return EditFileResponse(path=str(target), diff=diff, applied=applied)

    def create_directory(self, req: CreateDirectoryRequest) -> CreateDirectoryResponse:
        """Create a directory; returns as-is if the directory already exists."""
        target = self._resolve_safe(req.path)

        if req.dry_run:
            status = "exists" if target.exists() else "would create"
            return CreateDirectoryResponse(
                path=str(target), created=False, dry_run_info=status
            )

        # Capture existence before mkdir to determine the 'created' flag
        already_exists = target.exists()
        try:
            target.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise FileAuthorizationError(str(e))
        except OSError as e:
            logger.error("create_directory: OS error creating '%s': %s", target, e)
            raise FileValidationError(str(e))

        created = not already_exists
        return CreateDirectoryResponse(path=str(target), created=created)

    def move_file(self, req: MoveFileRequest) -> MoveFileResponse:
        """Move or rename a file or directory.

        Destination parent directory is created automatically if missing.
        """
        src = self._resolve_safe(req.source)
        dest = self._resolve_safe(req.destination)

        if req.dry_run:
            src_status = "exists" if src.exists() else "not found"
            dest_status = "exists (conflict)" if dest.exists() else "free"
            info = f"source={src_status}, dest={dest_status}"
            return MoveFileResponse(
                source=str(src),
                destination=str(dest),
                dry_run_info=info,
            )

        # Guard: source must exist before attempting the move
        if not src.exists():
            raise FileNotFoundError(
                f"Source does not exist: {req.source}",
            )

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
        except PermissionError as e:
            raise FileAuthorizationError(str(e))
        except OSError as e:
            logger.error("move_file: OS error moving '%s' to '%s': %s", src, dest, e)
            raise FileValidationError(str(e))

        return MoveFileResponse(source=str(src), destination=str(dest), dry_run_info="")

    # ── Dispatch handlers: format service results as plain text for the LLM ──

    async def fmt_write_file(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            lambda: self.write_file(WriteFileRequest(**args)),
        )
        return WriteFileFormatter.format_write_result(result)

    async def fmt_edit_file(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            lambda: self.edit_file(EditFileRequest(**args)),
        )
        return WriteFileFormatter.format_edit_result(result)

    async def fmt_create_directory(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            lambda: self.create_directory(CreateDirectoryRequest(**args)),
        )
        return WriteFileFormatter.format_directory_result(result)

    async def fmt_move_file(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            lambda: self.move_file(MoveFileRequest(**args)),
        )
        return WriteFileFormatter.format_move_result(result)

    def get_dispatch_table(
        self,
    ) -> dict[str, Callable[[ToolArgs], Awaitable[str]]]:
        """Build and return the MCP tool dispatch table keyed by tool name."""
        return {
            "write_file": self.fmt_write_file,
            "edit_file": self.fmt_edit_file,
            "create_directory": self.fmt_create_directory,
            "move_file": self.fmt_move_file,
        }


class WriteFileFormatter:
    """Format WriteFileService results as plain text for the LLM."""

    @staticmethod
    def format_write_result(result: WriteFileResponse) -> str:
        if not result.applied:
            info = f"Dry-run: {result.path} ({result.size} bytes)"
            if result.diff:
                info += f"\n{result.diff}"
            else:
                info += " [new file]"
            return info
        return f"Written: {result.path} ({result.size} bytes)"

    @staticmethod
    def format_edit_result(result: EditFileResponse) -> str:
        if not result.diff:
            return "No changes."
        if result.applied:
            return f"Edited\n{result.diff}"
        return f"Diff only (dry_run)\n{result.diff}"

    @staticmethod
    def format_directory_result(result: CreateDirectoryResponse) -> str:
        if result.dry_run_info:
            return f"Dry-run: {result.path} [{result.dry_run_info}]"
        status = "created" if result.created else "already exists"
        return f"Directory {status}: {result.path}"

    @staticmethod
    def format_move_result(result: MoveFileResponse) -> str:
        if result.dry_run_info:
            return f"Dry-run: {result.source} → {result.destination} [{result.dry_run_info}]"
        return f"Moved: {result.source} → {result.destination}"


def build_service(cfg: FileWriteConfig) -> WriteFileService:
    """Construct a WriteFileService from a typed config object."""
    allowed_dirs = [Path(d) for d in cfg.allowed_dirs]
    if not allowed_dirs:
        logger.warning("ALLOWED_DIRS is empty — all paths will be rejected")
    return WriteFileService(
        allowed_dirs=allowed_dirs,
        max_write_bytes=cfg.max_write_bytes,
    )
