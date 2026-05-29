#!/usr/bin/env python3
"""
file_write_mcp_service.py
WriteFileService business logic and lazy singleton proxy for file-write-mcp.

Dependency direction: file_write_mcp_models → file_write_mcp_service → file_write_mcp_server
"""

from __future__ import annotations

import asyncio
import difflib
import logging
import shutil
from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from mcp.file.common import require_file, resolve_safe
from mcp.file.write_models import (
    CreateDirectoryRequest,
    CreateDirectoryResponse,
    EditFileRequest,
    EditFileResponse,
    EditOperation,
    MoveFileRequest,
    MoveFileResponse,
    WriteFileRequest,
    WriteFileResponse,
    _get_cfg,
)
from mcp.server import ToolArgs

# Standard library logger; log path is owned by file_write_mcp_server.py
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
        """Apply each edit in order. Raises HTTPException 422 if old_text not found."""
        modified = content
        for i, op in enumerate(edits, start=1):
            if op.old_text not in modified:
                raise HTTPException(
                    status_code=422,
                    detail=(
                        f"Edit {i}: replacement target not found: {op.old_text[:80]!r}"
                    ),
                )
            modified = modified.replace(op.old_text, op.new_text, 1)
        return modified

    @staticmethod
    def _write_if_changed(
        target: Path, original: str, modified: str, dry_run: bool
    ) -> tuple[str, bool]:
        """Generate a unified diff and write the file if changed and not a dry run.
        Returns (diff_text, applied)."""
        diff_lines = difflib.unified_diff(
            original.splitlines(keepends=True),
            modified.splitlines(keepends=True),
            fromfile=f"a/{target.name}",
            tofile=f"b/{target.name}",
        )
        diff = "".join(diff_lines)
        applied = False
        if not dry_run and modified != original:
            try:
                target.write_text(modified, encoding="utf-8")
                applied = True
            except PermissionError as e:
                raise HTTPException(status_code=403, detail=str(e))
        return diff, applied

    # ── Business operation methods ──

    def write_file(self, req: WriteFileRequest) -> WriteFileResponse:
        """Create or overwrite a file; parent directories created automatically."""
        target = self._resolve_safe(req.path)
        size = len(req.content.encode("utf-8"))
        if req.dry_run:
            # Return diff against existing content without writing
            diff = ""
            if target.exists():
                try:
                    original = target.read_text(encoding="utf-8")
                    diff, _ = WriteFileService._write_if_changed(
                        target, original, req.content, True
                    )
                except (UnicodeDecodeError, PermissionError):
                    pass
            return WriteFileResponse(
                path=str(target), size=size, applied=False, diff=diff
            )
        try:
            # Ensure parent directory exists before writing
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(req.content, encoding="utf-8")
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except OSError as e:
            logger.error(f"write_file: OS error writing '{target}': {e}")
            raise HTTPException(status_code=400, detail=str(e))

        size = target.stat().st_size
        return WriteFileResponse(path=str(target), size=size, applied=True, diff="")

    def edit_file(self, req: EditFileRequest) -> EditFileResponse:
        """Apply string replacements to a file; dry_run returns only the diff."""
        target = self._resolve_safe(req.path)
        self._require_file(target, req.path)
        try:
            original = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=415, detail="File cannot be decoded as UTF-8"
            )
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        modified = WriteFileService._apply_text_edits(original, req.edits)
        diff, applied = WriteFileService._write_if_changed(
            target, original, modified, req.dry_run
        )
        return EditFileResponse(path=str(target), diff=diff, applied=applied)

    def create_directory(self, req: CreateDirectoryRequest) -> CreateDirectoryResponse:
        """Create a directory; returns as-is if the directory already exists."""
        target = self._resolve_safe(req.path)
        # Capture existence before mkdir to determine the 'created' flag
        already_exists = target.exists()
        try:
            target.mkdir(parents=True, exist_ok=True)
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except OSError as e:
            logger.error(f"create_directory: OS error creating '{target}': {e}")
            raise HTTPException(status_code=400, detail=str(e))

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
                source=str(src), destination=str(dest), dry_run_info=info
            )

        # Guard: source must exist before attempting the move
        if not src.exists():
            raise HTTPException(
                status_code=404, detail=f"Source does not exist: {req.source}"
            )

        try:
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(src), str(dest))
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except OSError as e:
            logger.error(f"move_file: OS error moving '{src}' to '{dest}': {e}")
            raise HTTPException(status_code=400, detail=str(e))

        return MoveFileResponse(source=str(src), destination=str(dest), dry_run_info="")

    # ── Dispatch handlers: format service results as plain text for the LLM ──

    async def fmt_write_file(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            lambda: self.write_file(WriteFileRequest(**args))
        )
        if not result.applied:
            info = f"Dry-run: {result.path} ({result.size} bytes)"
            if result.diff:
                info += f"\n{result.diff}"
            else:
                info += " [new file]"
            return info
        return f"Written: {result.path} ({result.size} bytes)"

    async def fmt_edit_file(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            lambda: self.edit_file(EditFileRequest(**args))
        )
        if not result.diff:
            return "No changes."
        if result.applied:
            return f"Edited\n{result.diff}"
        return f"Diff only (dry_run)\n{result.diff}"

    async def fmt_create_directory(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            lambda: self.create_directory(CreateDirectoryRequest(**args))
        )
        status = "created" if result.created else "already exists"
        return f"Directory {status}: {result.path}"

    async def fmt_move_file(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            lambda: self.move_file(MoveFileRequest(**args))
        )
        if result.dry_run_info:
            return f"Dry-run: {result.source} → {result.destination} [{result.dry_run_info}]"
        return f"Moved: {result.source} → {result.destination}"

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


class _LazyWriteFileService:
    """Lazy singleton proxy: defers WriteFileService init until first attribute access."""

    _instance: WriteFileService | None = None

    def __getattr__(self, name: str) -> Any:
        if _LazyWriteFileService._instance is None:
            cfg = _get_cfg()
            allowed_dirs = [Path(d) for d in cfg.get("allowed_dirs", [])]
            if not allowed_dirs:
                logger.warning("ALLOWED_DIRS is empty — all paths will be rejected")
            _LazyWriteFileService._instance = WriteFileService(
                allowed_dirs=allowed_dirs,
                max_write_bytes=cfg.get("max_write_bytes", 1048576),
            )
        return getattr(_LazyWriteFileService._instance, name)


# Singleton proxy; actual WriteFileService is created on first attribute access
_service: WriteFileService = _LazyWriteFileService()  # type: ignore[assignment]
