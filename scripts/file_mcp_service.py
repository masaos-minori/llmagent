#!/usr/bin/env python3
"""
file_mcp_service.py
FileService business logic and lazy singleton proxy for file_mcp_server.

Dependency direction: file_mcp_models → file_mcp_service → file_mcp_server
"""

import base64
import difflib
import fnmatch
import logging
import mimetypes
import re
import shutil
import stat as _stat
from collections.abc import Awaitable, Callable
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import HTTPException
from file_mcp_models import (
    CreateDirectoryRequest,
    CreateDirectoryResponse,
    DeleteDirectoryRequest,
    DeleteDirectoryResponse,
    DeleteFileRequest,
    DeleteFileResponse,
    DirectoryTreeRequest,
    DirectoryTreeResponse,
    EditFileRequest,
    EditFileResponse,
    EditOperation,
    FileEntry,
    FileInfo,
    FileResult,
    GetFileInfoRequest,
    GetFileInfoResponse,
    GrepFilesRequest,
    GrepFilesResponse,
    GrepMatch,
    ListDirectoryRequest,
    ListDirectoryResponse,
    MoveFileRequest,
    MoveFileResponse,
    ReadMediaFileRequest,
    ReadMediaFileResponse,
    ReadMultipleFilesRequest,
    ReadMultipleFilesResponse,
    ReadTextFileRequest,
    ReadTextFileResponse,
    SearchFilesRequest,
    SearchFilesResponse,
    TreeNode,
    WriteFileRequest,
    WriteFileResponse,
    _get_cfg,
)
from formatters import fmt_size
from mcp_server import ToolArgs

# Standard library logger; log path is owned by file_mcp_server.py
logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────────
# FileService: encapsulates filesystem operations with security boundaries
# ──────────────────────────────────────────────────────────────────────────────
class FileService:
    """Encapsulates filesystem operations with consistent security boundary checks."""

    def __init__(
        self,
        allowed_dirs: list[Path],
        max_read_bytes: int,
        max_write_bytes: int,
        max_tree_depth: int,
        max_search_results: int,
    ) -> None:
        self._allowed_dirs = allowed_dirs
        self._max_read_bytes = max_read_bytes
        self._max_write_bytes = max_write_bytes
        self._max_tree_depth = max_tree_depth
        self._max_search_results = max_search_results

    # ── Security helpers ──

    def _resolve_safe(self, raw_path: str) -> Path:
        """
        Normalize a path and check access permission.
        Resolve symlinks and ../ via realpath, then verify the path
        is under one of the allowed directories.
        Returns 403 for paths outside allowed directories.
        """
        # resolve() may raise OSError for dangling symlinks
        # (symlinks whose target does not exist); return 400 in that case.
        try:
            resolved = Path(raw_path).resolve()
        except OSError:
            raise HTTPException(status_code=400, detail="Invalid path")
        for allowed in self._allowed_dirs:
            try:
                resolved.relative_to(allowed.resolve())
                return resolved
            except ValueError:
                continue
        raise HTTPException(
            status_code=403,
            detail="Access denied: path is outside allowed directories",
        )

    def _require_file(self, target: Path, raw_path: str) -> None:
        """Raise 404 if target does not exist, 400 if it is not a regular file."""
        if not target.exists():
            raise HTTPException(
                status_code=404, detail=f"File does not exist: {raw_path}"
            )
        if not target.is_file():
            raise HTTPException(status_code=400, detail=f"Not a file: {raw_path}")

    def _require_dir(self, target: Path, raw_path: str) -> None:
        """Raise 404 if target does not exist, 400 if it is not a directory."""
        if not target.exists():
            raise HTTPException(
                status_code=404, detail=f"Path does not exist: {raw_path}"
            )
        if not target.is_dir():
            raise HTTPException(status_code=400, detail=f"Not a directory: {raw_path}")

    def _check_size_limit(self, target: Path) -> int:
        """Return file size in bytes, or raise 413 if it exceeds max_read_bytes."""
        try:
            size = target.stat().st_size
        except OSError as e:
            logger.error(f"_check_size_limit: stat failed for '{target}': {e}")
            raise HTTPException(status_code=400, detail=str(e))
        if size > self._max_read_bytes:
            raise HTTPException(
                status_code=413,
                detail=(
                    f"File size exceeds the limit"
                    f" ({self._max_read_bytes} bytes): {size} bytes"
                ),
            )
        return size

    # ── Static helpers (no instance state needed) ──

    @staticmethod
    def _build_tree(path: Path, current_depth: int, max_depth: int) -> TreeNode:
        """Recursively build a directory tree.

        When current_depth >= max_depth, directories are not expanded and
        depth_limited is set to True if the directory has any contents.
        """
        is_dir = path.is_dir()
        size = path.stat().st_size if path.is_file() else 0
        node = TreeNode(
            name=path.name,
            path=str(path),
            type="dir" if is_dir else "file",
            size=size,
            children=[],
        )
        if not is_dir:
            return node
        if current_depth < max_depth:
            try:
                for child in sorted(path.iterdir()):
                    node.children.append(
                        FileService._build_tree(child, current_depth + 1, max_depth)
                    )
            except PermissionError as e:
                logger.debug(f"Permission denied listing directory {path}: {e}")
        else:
            # Mark as depth-limited when the directory has contents that were omitted
            try:
                node.depth_limited = any(path.iterdir())
            except PermissionError:
                pass
        return node

    @staticmethod
    def _count_tree_nodes(node: TreeNode) -> int:
        """Count the total number of nodes in the tree."""
        return 1 + sum(FileService._count_tree_nodes(c) for c in node.children)

    @staticmethod
    def _format_permissions(mode: int) -> str:
        """Return a 9-character rwx string (e.g. 'rwxr-xr-x') from a stat mode int."""
        return _stat.filemode(mode)[1:]

    @staticmethod
    def _slice_lines(content: str, head: int | None, tail: int | None) -> str:
        """Return a line-sliced view of content using head or tail.
        No-op when both are None."""
        if head is None and tail is None:
            return content
        all_lines = content.splitlines(keepends=True)
        if head is not None:
            return "".join(all_lines[:head])
        # model_validator guarantees tail is not None when head is None
        assert tail is not None
        return "".join(all_lines[-tail:])

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

    def list_dir_entries(
        self, req: ListDirectoryRequest, include_dir_sizes: bool
    ) -> ListDirectoryResponse:
        """
        Shared implementation for list_directory and list_directory_with_sizes.
        Validates the path, iterates directory entries, and returns a response.

        include_dir_sizes=False: directory size is reported as 0 (list_directory).
        include_dir_sizes=True:  directory size is taken from stat st_size
                                 (list_directory_with_sizes).
        """
        target = self._resolve_safe(req.path)
        self._require_dir(target, req.path)

        entries: list[FileEntry] = []
        try:
            for child in sorted(target.iterdir()):
                # When include_dir_sizes is False, report directory size as 0.
                # When True, use stat st_size (the directory entry's own block size).
                size = (
                    child.stat().st_size
                    if (child.is_file() or include_dir_sizes)
                    else 0
                )
                entries.append(
                    FileEntry(
                        name=child.name,
                        path=str(child),
                        type="dir" if child.is_dir() else "file",
                        size=size,
                    )
                )
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))

        return ListDirectoryResponse(path=str(target), entries=entries)

    def build_directory_tree(self, req: DirectoryTreeRequest) -> DirectoryTreeResponse:
        """Build a recursive directory tree, clamped to max_tree_depth."""
        target = self._resolve_safe(req.path)
        self._require_dir(target, req.path)
        depth = min(req.depth, self._max_tree_depth)
        tree = FileService._build_tree(target, current_depth=0, max_depth=depth)
        return DirectoryTreeResponse(root=tree)

    def read_text_file(self, req: ReadTextFileRequest) -> ReadTextFileResponse:
        """Return the contents of the specified file as UTF-8 text."""
        target = self._resolve_safe(req.path)
        self._require_file(target, req.path)
        size = self._check_size_limit(target)

        try:
            raw_content = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise HTTPException(
                status_code=415, detail="File cannot be decoded as UTF-8"
            )
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))

        content = FileService._slice_lines(raw_content, req.head, req.tail)
        return ReadTextFileResponse(path=str(target), content=content, size=size)

    def read_media_file(self, req: ReadMediaFileRequest) -> ReadMediaFileResponse:
        """Read the specified file as binary and return it base64-encoded."""
        target = self._resolve_safe(req.path)
        self._require_file(target, req.path)
        size = self._check_size_limit(target)

        try:
            data = target.read_bytes()
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except OSError as e:
            logger.error(f"read_media_file: OS error reading '{target}': {e}")
            raise HTTPException(status_code=400, detail=str(e))

        # Fall back to application/octet-stream when the MIME type cannot be determined
        mime_type, _ = mimetypes.guess_type(str(target))
        if mime_type is None:
            mime_type = "application/octet-stream"

        return ReadMediaFileResponse(
            path=str(target),
            content_base64=base64.b64encode(data).decode("ascii"),
            mime_type=mime_type,
            size=size,
        )

    def read_single_file(self, raw_path: str) -> FileResult:
        """Read one file and return a FileResult.
        Errors are captured in FileResult.error rather than raised."""
        try:
            target = self._resolve_safe(raw_path)
            size = target.stat().st_size
            if size > self._max_read_bytes:
                return FileResult(
                    path=raw_path,
                    content=None,
                    error=f"Size limit exceeded: {size} bytes",
                )
            content = target.read_text(encoding="utf-8")
            return FileResult(path=str(target), content=content, size=size)
        except HTTPException as e:
            return FileResult(path=raw_path, content=None, error=e.detail)
        except UnicodeDecodeError:
            return FileResult(
                path=raw_path, content=None, error="File cannot be decoded as UTF-8"
            )
        except OSError as e:
            logger.warning(f"read_multiple_files: OS error reading '{raw_path}': {e}")
            return FileResult(path=raw_path, content=None, error=str(e))

    def read_multiple_files(
        self, req: ReadMultipleFilesRequest
    ) -> ReadMultipleFilesResponse:
        """Retrieve multiple files; continues even if individual errors occur."""
        results = [self.read_single_file(raw_path) for raw_path in req.paths]
        return ReadMultipleFilesResponse(results=results)

    def write_file(self, req: WriteFileRequest) -> WriteFileResponse:
        """Create or overwrite a file; parent directories created automatically."""
        target = self._resolve_safe(req.path)
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
        return WriteFileResponse(path=str(target), size=size)

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
        modified = FileService._apply_text_edits(original, req.edits)
        diff, applied = FileService._write_if_changed(
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

        return MoveFileResponse(source=str(src), destination=str(dest))

    def search_files(self, req: SearchFilesRequest) -> SearchFilesResponse:
        """Recursively search for files matching a glob pattern within a directory."""
        base = self._resolve_safe(req.path)
        self._require_dir(base, req.path)

        matches: list[str] = []
        try:
            for p in base.rglob("*"):
                if len(matches) >= self._max_search_results:
                    break
                if fnmatch.fnmatch(p.name, req.pattern):
                    matches.append(str(p))
        except PermissionError as e:
            logger.debug(f"Permission denied during file search in {base}: {e}")

        return SearchFilesResponse(pattern=req.pattern, matches=matches)

    def _collect_grep_matches(
        self,
        base: Path,
        compiled: re.Pattern[str],
        file_pattern: str,
        max_matches: int,
    ) -> tuple[list[GrepMatch], bool]:
        """Walk base recursively, match lines against compiled.
        Returns (matches, truncated) where truncated=True when max_matches reached."""
        matches: list[GrepMatch] = []
        try:
            for p in sorted(base.rglob("*")):
                if not p.is_file() or not fnmatch.fnmatch(p.name, file_pattern):
                    continue
                try:
                    text = p.read_text(encoding="utf-8")
                except (UnicodeDecodeError, PermissionError):
                    continue
                for lineno, line in enumerate(text.splitlines(), start=1):
                    if compiled.search(line):
                        matches.append(
                            GrepMatch(
                                file=str(p), line_number=lineno, line=line.rstrip()
                            )
                        )
                        if len(matches) >= max_matches:
                            return matches, True
        except PermissionError as e:
            logger.warning(
                f"grep_files: directory traversal stopped due to permission error: {e}"
            )
        return matches, False

    def grep_files(self, req: GrepFilesRequest) -> GrepFilesResponse:
        """Search file contents under a directory using a regex pattern."""
        base = self._resolve_safe(req.path)
        self._require_dir(base, req.path)
        try:
            compiled = re.compile(req.pattern)
        except re.error as e:
            raise HTTPException(
                status_code=400, detail=f"Invalid regular expression: {e}"
            )
        matches, truncated = self._collect_grep_matches(
            base, compiled, req.file_pattern, req.max_matches
        )
        return GrepFilesResponse(
            pattern=req.pattern, matches=matches, truncated=truncated
        )

    def get_file_info(self, req: GetFileInfoRequest) -> GetFileInfoResponse:
        """Return metadata (size, timestamps, permissions) for a file or directory."""
        target = self._resolve_safe(req.path)
        # Guard: path must exist before calling stat()
        if not target.exists():
            raise HTTPException(
                status_code=404, detail=f"Path does not exist: {req.path}"
            )

        try:
            st = target.stat()
        except OSError as e:
            logger.error(f"get_file_info: stat failed for '{target}': {e}")
            raise HTTPException(status_code=400, detail=str(e))

        perms = FileService._format_permissions(st.st_mode)
        info = FileInfo(
            path=str(target),
            name=target.name,
            type="dir" if target.is_dir() else "file",
            size=st.st_size,
            created_at=datetime.fromtimestamp(st.st_ctime).isoformat(),
            modified_at=datetime.fromtimestamp(st.st_mtime).isoformat(),
            permissions=perms,
        )
        return GetFileInfoResponse(info=info)

    def delete_file(self, req: DeleteFileRequest) -> DeleteFileResponse:
        """Delete the specified file."""
        target = self._resolve_safe(req.path)
        self._require_file(target, req.path)
        try:
            target.unlink()
        except PermissionError as e:
            raise HTTPException(status_code=403, detail=str(e))
        except OSError as e:
            logger.error(f"delete_file: OS error deleting '{target}': {e}")
            raise HTTPException(status_code=400, detail=str(e))

        return DeleteFileResponse(path=str(target), deleted=True)

    def delete_directory(self, req: DeleteDirectoryRequest) -> DeleteDirectoryResponse:
        """Delete a directory; raises if not empty when recursive=false."""
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

        return DeleteDirectoryResponse(path=str(target), deleted=True)

    # ── Dispatch helpers ──

    @staticmethod
    def _has_depth_limit(node: "TreeNode") -> bool:
        """Return True if any node in the tree was truncated by the depth limit."""
        if node.depth_limited:
            return True
        return any(FileService._has_depth_limit(c) for c in node.children)

    @staticmethod
    def _fmt_tree_node(node: "TreeNode", indent: int = 0) -> str:
        """Recursively format a directory tree node with type and size annotations."""
        prefix = "  " * indent
        if node.type == "dir":
            depth_note = " (depth limit reached)" if node.depth_limited else ""
            size_note = f" ({fmt_size(node.size)})" if node.size > 0 else ""
            line = f"{prefix}[DIR] {node.name}/{size_note}{depth_note}"
        else:
            line = f"{prefix}[FILE] {node.name} ({fmt_size(node.size)})"
        lines: list[str] = [line]
        for child in node.children:
            lines.append(FileService._fmt_tree_node(child, indent + 1))
        return "\n".join(lines)

    @staticmethod
    def _fmt_dir_entries(entries: "list[FileEntry]") -> str:
        """Format a list of FileEntry objects into a human-readable string."""
        if not entries:
            return "(empty directory)"
        lines = [
            f"{'[DIR]' if e.type == 'dir' else '[FILE]'} {e.name} ({fmt_size(e.size)})"
            for e in entries
        ]
        return f"[{len(entries)} entries]\n" + "\n".join(lines)

    # ── Dispatch handlers: format service results as plain text for the LLM ──

    async def fmt_list_directory(self, args: ToolArgs) -> str:
        result = self.list_dir_entries(
            ListDirectoryRequest(**args), include_dir_sizes=False
        )
        return FileService._fmt_dir_entries(result.entries)

    async def fmt_list_directory_with_sizes(self, args: ToolArgs) -> str:
        result = self.list_dir_entries(
            ListDirectoryRequest(**args), include_dir_sizes=True
        )
        return FileService._fmt_dir_entries(result.entries)

    async def fmt_directory_tree(self, args: ToolArgs) -> str:
        result = self.build_directory_tree(DirectoryTreeRequest(**args))
        effective_depth = min(args.get("depth", 3), self._max_tree_depth)
        total_nodes = FileService._count_tree_nodes(result.root)
        trunc_note = ", truncated" if FileService._has_depth_limit(result.root) else ""
        header = f"[Tree: {total_nodes} nodes, depth={effective_depth}{trunc_note}]\n"
        return header + FileService._fmt_tree_node(result.root)

    async def fmt_read_text_file(self, args: ToolArgs) -> str:
        result = self.read_text_file(ReadTextFileRequest(**args))
        return result.content

    async def fmt_read_media_file(self, args: ToolArgs) -> str:
        result = self.read_media_file(ReadMediaFileRequest(**args))
        return f"base64:{result.mime_type};{result.content_base64}"

    async def fmt_read_multiple_files(self, args: ToolArgs) -> str:
        result = self.read_multiple_files(ReadMultipleFilesRequest(**args))
        parts = [
            f"=== {r.path} [ERROR: {r.error}] ==="
            if r.error is not None
            else f"=== {r.path} ({r.size} bytes) ===\n{r.content}"
            for r in result.results
        ]
        return "\n\n".join(parts) if parts else "(no files)"

    async def fmt_write_file(self, args: ToolArgs) -> str:
        result = self.write_file(WriteFileRequest(**args))
        return f"Written: {result.path} ({result.size} bytes)"

    async def fmt_edit_file(self, args: ToolArgs) -> str:
        result = self.edit_file(EditFileRequest(**args))
        if not result.diff:
            return "No changes."
        if result.applied:
            return f"Edited\n{result.diff}"
        return f"Diff only (dry_run)\n{result.diff}"

    async def fmt_create_directory(self, args: ToolArgs) -> str:
        result = self.create_directory(CreateDirectoryRequest(**args))
        status = "created" if result.created else "already exists"
        return f"Directory {status}: {result.path}"

    async def fmt_move_file(self, args: ToolArgs) -> str:
        result = self.move_file(MoveFileRequest(**args))
        return f"Moved: {result.source} → {result.destination}"

    async def fmt_search_files(self, args: ToolArgs) -> str:
        result = self.search_files(SearchFilesRequest(**args))
        return (
            "\n".join(result.matches) if result.matches else "No matching files found."
        )

    async def fmt_grep_files(self, args: ToolArgs) -> str:
        result = self.grep_files(GrepFilesRequest(**args))
        if not result.matches:
            return "No matches found."
        lines = [f"{m.file}:{m.line_number}: {m.line}" for m in result.matches]
        text = "\n".join(lines)
        if result.truncated:
            text += "\n... (truncated)"
        return text

    async def fmt_delete_file(self, args: ToolArgs) -> str:
        result = self.delete_file(DeleteFileRequest(**args))
        return f"Deleted: {result.path}"

    async def fmt_delete_directory(self, args: ToolArgs) -> str:
        result = self.delete_directory(DeleteDirectoryRequest(**args))
        return f"Directory deleted: {result.path}"

    async def fmt_get_file_info(self, args: ToolArgs) -> str:
        result = self.get_file_info(GetFileInfoRequest(**args))
        info = result.info
        return "\n".join(
            [
                f"path: {info.path}",
                f"name: {info.name}",
                f"type: {info.type}",
                f"size: {info.size}",
                f"created_at: {info.created_at}",
                f"modified_at: {info.modified_at}",
                f"permissions: {info.permissions}",
            ]
        )

    def get_dispatch_table(
        self,
    ) -> dict[str, Callable[[ToolArgs], Awaitable[str]]]:
        """Build and return the MCP tool dispatch table keyed by tool name."""
        return {
            "list_directory": self.fmt_list_directory,
            "list_directory_with_sizes": self.fmt_list_directory_with_sizes,
            "directory_tree": self.fmt_directory_tree,
            "read_text_file": self.fmt_read_text_file,
            "read_media_file": self.fmt_read_media_file,
            "read_multiple_files": self.fmt_read_multiple_files,
            "write_file": self.fmt_write_file,
            "edit_file": self.fmt_edit_file,
            "create_directory": self.fmt_create_directory,
            "move_file": self.fmt_move_file,
            "search_files": self.fmt_search_files,
            "grep_files": self.fmt_grep_files,
            "delete_file": self.fmt_delete_file,
            "delete_directory": self.fmt_delete_directory,
            "get_file_info": self.fmt_get_file_info,
        }


class _LazyFileService:
    """Lazy singleton proxy: defers FileService init until first attribute access."""

    _instance: "FileService | None" = None

    def __getattr__(self, name: str) -> Any:
        if _LazyFileService._instance is None:
            cfg = _get_cfg()
            allowed_dirs = [Path(d) for d in cfg.get("allowed_dirs", [])]
            if not allowed_dirs:
                logger.warning("ALLOWED_DIRS is empty — all paths will be rejected")
            _LazyFileService._instance = FileService(
                allowed_dirs=allowed_dirs,
                max_read_bytes=cfg.get("max_read_bytes", 1048576),
                max_write_bytes=cfg.get("max_write_bytes", 1048576),
                max_tree_depth=cfg.get("max_tree_depth", 5),
                max_search_results=cfg.get("max_search_results", 100),
            )
        return getattr(_LazyFileService._instance, name)


# Singleton proxy; actual FileService is created on first attribute access
_service: FileService = _LazyFileService()  # type: ignore[assignment]
