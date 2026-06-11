#!/usr/bin/env python3
"""file_read_mcp_service.py
ReadFileService business logic and lazy singleton proxy for file-read-mcp.

Dependency direction: file_read_mcp_models → file_read_mcp_service → file_read_mcp_server
"""

from __future__ import annotations

import asyncio
import base64
import fnmatch
import logging
import mimetypes
import re
from collections.abc import Awaitable, Callable
from datetime import datetime
from pathlib import Path

from shared.formatters import fmt_size

from mcp.file.common import (
    FileAuthorizationError,
    FileValidationError,
    check_size_limit,
    format_permissions,
    require_dir,
    require_file,
    resolve_safe,
)
from mcp.file.read_models import (
    DirectoryTreeRequest,
    DirectoryTreeResponse,
    FileEntry,
    FileInfo,
    FileReadConfig,
    FileResult,
    GetFileInfoRequest,
    GetFileInfoResponse,
    GrepFilesRequest,
    GrepFilesResponse,
    GrepMatch,
    ListDirectoryRequest,
    ListDirectoryResponse,
    ReadMediaFileRequest,
    ReadMediaFileResponse,
    ReadMultipleFilesRequest,
    ReadMultipleFilesResponse,
    ReadTextFileRequest,
    ReadTextFileResponse,
    SearchFilesRequest,
    SearchFilesResponse,
    TreeNode,
)
from mcp.server import ToolArgs

# Standard library logger; log path is owned by mcp/file/read_server.py
logger = logging.getLogger(__name__)


class ReadFileService:
    """Encapsulates read-only filesystem operations with consistent security boundaries."""

    def __init__(
        self,
        allowed_dirs: list[Path],
        max_read_bytes: int,
        max_tree_depth: int,
        max_search_results: int,
    ) -> None:
        self._allowed_dirs = allowed_dirs
        self._max_read_bytes = max_read_bytes
        self._max_tree_depth = max_tree_depth
        self._max_search_results = max_search_results

    @property
    def max_tree_depth(self) -> int:
        """Maximum tree recursion depth configured for this service."""
        return self._max_tree_depth

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

    # ── Static helpers ──

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
                        ReadFileService._build_tree(
                            child, current_depth + 1, max_depth
                        ),
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
        return 1 + sum(ReadFileService._count_tree_nodes(c) for c in node.children)

    @staticmethod
    def _slice_lines(content: str, head: int | None, tail: int | None) -> str:
        """Return a line-sliced view of content using head or tail. No-op when both are None."""
        if head is None and tail is None:
            return content
        all_lines = content.splitlines(keepends=True)
        if head is not None:
            return "".join(all_lines[:head])
        # model_validator guarantees tail is not None when head is None
        if tail is None:
            return content
        return "".join(all_lines[-tail:])

    @staticmethod
    def _fmt_tree_node(node: TreeNode, indent: int = 0) -> str:
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
            lines.append(ReadFileService._fmt_tree_node(child, indent + 1))
        return "\n".join(lines)

    @staticmethod
    def _fmt_dir_entries(entries: list[FileEntry]) -> str:
        """Format a list of FileEntry objects into a human-readable string."""
        if not entries:
            return "(empty directory)"
        lines = [
            f"{'[DIR]' if e.type == 'dir' else '[FILE]'} {e.name} ({fmt_size(e.size)})"
            for e in entries
        ]
        return f"[{len(entries)} entries]\n" + "\n".join(lines)

    # ── Business operation methods ──

    def list_dir_entries(
        self,
        req: ListDirectoryRequest,
        include_dir_sizes: bool,
    ) -> ListDirectoryResponse:
        """Validate path, iterate directory entries, and return a response.

        include_dir_sizes=False: directory size is reported as 0 (list_directory).
        include_dir_sizes=True:  directory size is taken from stat st_size
                                 (list_directory_with_sizes).
        """
        target = self._resolve_safe(req.path)
        self._require_dir(target, req.path)

        entries: list[FileEntry] = []
        try:
            for child in sorted(target.iterdir()):
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
                    ),
                )
        except PermissionError as e:
            raise FileAuthorizationError(str(e))

        return ListDirectoryResponse(path=str(target), entries=entries)

    def build_directory_tree(self, req: DirectoryTreeRequest) -> DirectoryTreeResponse:
        """Build a recursive directory tree, clamped to max_tree_depth."""
        target = self._resolve_safe(req.path)
        self._require_dir(target, req.path)
        depth = min(req.depth, self._max_tree_depth)
        tree = ReadFileService._build_tree(target, current_depth=0, max_depth=depth)
        return DirectoryTreeResponse(root=tree)

    def read_text_file(self, req: ReadTextFileRequest) -> ReadTextFileResponse:
        """Return the contents of the specified file as UTF-8 text."""
        target = self._resolve_safe(req.path)
        self._require_file(target, req.path)
        size = self._check_size_limit(target)

        try:
            raw_content = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise FileValidationError(
                "File cannot be decoded as UTF-8",
            )
        except PermissionError as e:
            raise FileAuthorizationError(str(e))

        content = ReadFileService._slice_lines(raw_content, req.head, req.tail)
        return ReadTextFileResponse(path=str(target), content=content, size=size)

    def read_media_file(self, req: ReadMediaFileRequest) -> ReadMediaFileResponse:
        """Read the specified file as binary and return it base64-encoded."""
        target = self._resolve_safe(req.path)
        self._require_file(target, req.path)
        size = self._check_size_limit(target)

        try:
            data = target.read_bytes()
        except PermissionError as e:
            raise FileAuthorizationError(str(e))
        except OSError as e:
            logger.error(f"read_media_file: OS error reading '{target}': {e}")
            raise FileValidationError(str(e))

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
        """Read one file and return a FileResult. Errors are captured in FileResult.error."""
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
        except (FileAuthorizationError, FileValidationError) as e:
            return FileResult(path=raw_path, content=None, error=str(e))
        except UnicodeDecodeError:
            return FileResult(
                path=raw_path,
                content=None,
                error="File cannot be decoded as UTF-8",
            )
        except OSError as e:
            logger.warning(f"read_multiple_files: OS error reading '{raw_path}': {e}")
            return FileResult(path=raw_path, content=None, error=str(e))

    def read_multiple_files(
        self,
        req: ReadMultipleFilesRequest,
    ) -> ReadMultipleFilesResponse:
        """Retrieve multiple files; continues even if individual errors occur."""
        results = [self.read_single_file(raw_path) for raw_path in req.paths]
        return ReadMultipleFilesResponse(results=results)

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
        Returns (matches, truncated) where truncated=True when max_matches reached.
        """
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
                                file=str(p),
                                line_number=lineno,
                                line=line.rstrip(),
                            ),
                        )
                        if len(matches) >= max_matches:
                            return matches, True
        except PermissionError as e:
            logger.warning(
                f"grep_files: directory traversal stopped due to permission error: {e}",
            )
        return matches, False

    def grep_files(self, req: GrepFilesRequest) -> GrepFilesResponse:
        """Search file contents under a directory using a regex pattern."""
        base = self._resolve_safe(req.path)
        self._require_dir(base, req.path)
        try:
            compiled = re.compile(req.pattern)
        except re.error as e:
            raise FileValidationError(
                f"Invalid regular expression: {e}",
            )
        matches, truncated = self._collect_grep_matches(
            base,
            compiled,
            req.file_pattern,
            req.max_matches,
        )
        return GrepFilesResponse(
            pattern=req.pattern,
            matches=matches,
            truncated=truncated,
        )

    def get_file_info(self, req: GetFileInfoRequest) -> GetFileInfoResponse:
        """Return metadata (size, timestamps, permissions) for a file or directory."""
        target = self._resolve_safe(req.path)
        # Guard: path must exist before calling stat()
        if not target.exists():
            raise FileNotFoundError(
                f"Path does not exist: {req.path}",
            )

        try:
            st = target.stat()
        except OSError as e:
            logger.error(f"get_file_info: stat failed for '{target}': {e}")
            raise FileValidationError(str(e))

        perms = format_permissions(st.st_mode)
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

    # ── Dispatch helpers ──

    @staticmethod
    def _has_depth_limit(node: TreeNode) -> bool:
        """Return True if any node in the tree was truncated by the depth limit."""
        if node.depth_limited:
            return True
        return any(ReadFileService._has_depth_limit(c) for c in node.children)

    # ── Dispatch handlers: format service results as plain text for the LLM ──

    async def fmt_list_directory(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            self.list_dir_entries,
            ListDirectoryRequest(**args),
            include_dir_sizes=False,
        )
        return ReadFileService._fmt_dir_entries(result.entries)

    async def fmt_list_directory_with_sizes(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            self.list_dir_entries,
            ListDirectoryRequest(**args),
            include_dir_sizes=True,
        )
        return ReadFileService._fmt_dir_entries(result.entries)

    async def fmt_directory_tree(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            lambda: self.build_directory_tree(DirectoryTreeRequest(**args)),
        )
        effective_depth = min(args.get("depth", 3), self._max_tree_depth)
        total_nodes = ReadFileService._count_tree_nodes(result.root)
        trunc_note = (
            ", truncated" if ReadFileService._has_depth_limit(result.root) else ""
        )
        header = f"[Tree: {total_nodes} nodes, depth={effective_depth}{trunc_note}]\n"
        return header + ReadFileService._fmt_tree_node(result.root)

    async def fmt_read_text_file(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            lambda: self.read_text_file(ReadTextFileRequest(**args)),
        )
        return result.content

    async def fmt_read_media_file(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            lambda: self.read_media_file(ReadMediaFileRequest(**args)),
        )
        return f"base64:{result.mime_type};{result.content_base64}"

    async def fmt_read_multiple_files(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            lambda: self.read_multiple_files(ReadMultipleFilesRequest(**args)),
        )
        parts = [
            f"=== {r.path} [ERROR: {r.error}] ==="
            if r.error is not None
            else f"=== {r.path} ({r.size} bytes) ===\n{r.content}"
            for r in result.results
        ]
        return "\n\n".join(parts) if parts else "(no files)"

    async def fmt_search_files(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            lambda: self.search_files(SearchFilesRequest(**args)),
        )
        return (
            "\n".join(result.matches) if result.matches else "No matching files found."
        )

    async def fmt_grep_files(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            lambda: self.grep_files(GrepFilesRequest(**args)),
        )
        if not result.matches:
            return "No matches found."
        lines = [f"{m.file}:{m.line_number}: {m.line}" for m in result.matches]
        text = "\n".join(lines)
        if result.truncated:
            text += "\n... (truncated)"
        return text

    async def fmt_get_file_info(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            lambda: self.get_file_info(GetFileInfoRequest(**args)),
        )
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
            ],
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
            "search_files": self.fmt_search_files,
            "grep_files": self.fmt_grep_files,
            "get_file_info": self.fmt_get_file_info,
        }


def build_service(cfg: FileReadConfig) -> ReadFileService:
    """Construct a ReadFileService from a typed config object."""
    allowed_dirs = [Path(d) for d in cfg.allowed_dirs]
    if not allowed_dirs:
        logger.warning("ALLOWED_DIRS is empty — all paths will be rejected")
    return ReadFileService(
        allowed_dirs=allowed_dirs,
        max_read_bytes=cfg.max_file_size_kb * 1024,
        max_tree_depth=cfg.max_depth,
        max_search_results=cfg.max_files_per_batch,
    )
