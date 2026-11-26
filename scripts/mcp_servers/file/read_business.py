#!/usr/bin/env python3
"""scripts/mcp_servers/file/read_business.py

ReadFileService business operations for file-read-mcp.

Dependency direction: read_business → read_models, common, read_static_helpers
Import from here:  from mcp_servers.file.read_business import ReadFileService
"""

from __future__ import annotations

import base64
import fnmatch
import logging
import mimetypes
import re
import time
from datetime import datetime
from pathlib import Path

from mcp_servers.file.common import (
    FileAuthorizationError,
    FileValidationError,
    format_permissions,
)
from mcp_servers.file.read_models import (
    DirectoryTreeRequest,
    DirectoryTreeResponse,
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
    ReadMediaFileRequest,
    ReadMediaFileResponse,
    ReadMultipleFilesRequest,
    ReadMultipleFilesResponse,
    ReadTextFileRequest,
    ReadTextFileResponse,
    SearchFilesRequest,
    SearchFilesResponse,
    TruncationReason,
)
from mcp_servers.file.read_security import ReadSecurityGuards
from mcp_servers.file.read_static_helpers import (
    TraversalState,
    build_tree,
    slice_lines,
)

logger = logging.getLogger(__name__)


class ReadFileService(ReadSecurityGuards):
    """Encapsulates read-only filesystem operations with consistent security boundaries."""

    def __init__(
        self,
        allowed_dirs: list[Path],
        max_read_bytes: int,
        max_tree_depth: int,
        max_search_results: int,
        max_tree_nodes: int = 2000,
        max_scanned_files: int = 5000,
        max_total_scan_bytes: int = 10485760,
        traversal_deadline_sec: float = 10.0,
    ) -> None:
        """Initialize the read file service with security guards and operation limits."""
        ReadSecurityGuards.__init__(self, allowed_dirs, max_read_bytes)
        self._max_tree_depth = max_tree_depth
        self._max_search_results = max_search_results
        self._max_tree_nodes = max_tree_nodes
        self._max_scanned_files = max_scanned_files
        self._max_total_scan_bytes = max_total_scan_bytes
        self._traversal_deadline_sec = traversal_deadline_sec

    @property
    def max_tree_depth(self) -> int:
        """Maximum tree recursion depth configured for this service."""
        return self._max_tree_depth

    # ── Business operation methods ──

    @staticmethod
    def _entry_size_or_skip(child: Path, include_dir_sizes: bool) -> int | None:
        """Compute a directory entry's size, or None if the entry should be skipped.

        Returns 0 without stat-ing when the entry is a directory and
        include_dir_sizes is False. Returns None (skip signal) if stat() fails.
        """
        if not (child.is_file() or include_dir_sizes):
            return 0
        try:
            return child.stat().st_size
        except OSError as e:
            logger.warning("list_dir_entries: stat error for '%s': %s", child, e)
            return None

    def list_dir_entries(
        self,
        req: ListDirectoryRequest,
        include_dir_sizes: bool,
    ) -> ListDirectoryResponse:
        """Validate path, iterate directory entries, and return a response."""
        target = self._resolve_safe(req.path)
        self._require_dir(target, req.path)

        entries: list[FileEntry] = []
        try:
            for child in sorted(target.iterdir()):
                size = self._entry_size_or_skip(child, include_dir_sizes)
                if size is None:
                    continue
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
        """Build a recursive directory tree, clamped to max_tree_depth and node limit."""
        target = self._resolve_safe(req.path)
        self._require_dir(target, req.path)
        depth = min(req.depth, self._max_tree_depth)
        state = TraversalState()
        tree = build_tree(
            target,
            current_depth=0,
            max_depth=depth,
            max_tree_nodes=self._max_tree_nodes,
            state=state,
        )
        return DirectoryTreeResponse(root=tree, truncation_reason=state.reason)

    def read_text_file(self, req: ReadTextFileRequest) -> ReadTextFileResponse:
        """Return the contents of the specified file as UTF-8 text."""
        target, size = self._validate_file(req.path, expected_type="file")

        try:
            raw_content = target.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            raise FileValidationError("File cannot be decoded as UTF-8")
        except PermissionError as e:
            raise FileAuthorizationError(str(e))

        content = slice_lines(raw_content, req.head, req.tail)
        return ReadTextFileResponse(path=str(target), content=content, size=size)

    def read_media_file(self, req: ReadMediaFileRequest) -> ReadMediaFileResponse:
        """Read the specified file as binary and return it base64-encoded."""
        target, size = self._validate_file(req.path, expected_type="file")

        data = self._read_media_data(target)
        mime_type = self._guess_mime_type(target)

        return ReadMediaFileResponse(
            path=str(target),
            content_base64=base64.b64encode(data).decode("ascii"),
            mime_type=mime_type,
            size=size,
        )

    def _read_media_data(self, target: Path) -> bytes:
        """Read binary file data. Raises FileAuthorizationError/FileValidationError on error."""
        try:
            return target.read_bytes()
        except PermissionError as e:
            raise FileAuthorizationError(str(e))
        except OSError as e:
            logger.error("read_media_file: OS error reading '%s': %s", target, e)
            raise FileValidationError(str(e))

    @staticmethod
    def _guess_mime_type(target: Path) -> str:
        """Guess MIME type for a file. Returns 'application/octet-stream' if unknown."""
        mime_type, _ = mimetypes.guess_type(str(target))
        return mime_type or "application/octet-stream"

    def read_single_file(self, raw_path: str) -> FileResult:
        """Read one file and return a FileResult. Errors are captured in FileResult.error."""
        try:
            target = self._resolve_safe(raw_path)
        except (FileAuthorizationError, FileValidationError) as e:
            return FileResult(path=raw_path, content=None, error=str(e))
        size = target.stat().st_size
        if size > self._max_read_bytes:
            # FileResult has no truncation_reason field (seq 01 added the field only to
            # traversal responses), so the structured reason is reported in the error text.
            return FileResult(
                path=raw_path,
                content=None,
                error=f"Size limit exceeded: {size} bytes (byte_limit)",
            )
        try:
            content = target.read_text(encoding="utf-8")
            return FileResult(path=str(target), content=content, size=size)
        except UnicodeDecodeError:
            return FileResult(
                path=raw_path,
                content=None,
                error="File cannot be decoded as UTF-8",
            )
        except PermissionError as e:
            return FileResult(path=raw_path, content=None, error=str(e))
        except OSError as e:
            logger.warning(
                "read_multiple_files: OS error reading '%s': %s", raw_path, e
            )
            return FileResult(path=raw_path, content=None, error=str(e))

    def read_multiple_files(
        self, req: ReadMultipleFilesRequest
    ) -> ReadMultipleFilesResponse:
        """Retrieve multiple files; continues even if individual errors occur."""
        results = [self.read_single_file(raw_path) for raw_path in req.paths]
        return ReadMultipleFilesResponse(results=results)

    def search_files(self, req: SearchFilesRequest) -> SearchFilesResponse:
        """Recursively search for files matching a glob pattern within a directory.

        Symlink entries are skipped before any stat() call (REQ-002). The scan is
        bounded by max_scanned_files, max_total_scan_bytes, and the traversal
        deadline; whichever limit stops the traversal is reported as the structured
        truncation reason (REQ-003).
        """
        base = self._resolve_safe(req.path)
        self._require_dir(base, req.path)

        matches: list[str] = []
        reason: TruncationReason | None = None
        scanned_files = 0
        total_bytes = 0
        deadline = time.monotonic() + self._traversal_deadline_sec

        # PermissionError during rglob() traversal is swallowed by glob.py itself
        # (CPython v3.13+ Lib/glob.py: scandir() OSError caught in except OSError: pass).
        # See plans/20260817-161921_plan.md
        for p in base.rglob("*"):
            if p.is_symlink():
                continue
            if len(matches) >= self._max_search_results:
                break
            if time.monotonic() > deadline:
                reason = "deadline"
                break
            if p.is_file():
                scanned_files += 1
                if scanned_files > self._max_scanned_files:
                    reason = "scanned_file_limit"
                    break
                try:
                    total_bytes += p.stat().st_size
                except OSError:
                    continue
                if total_bytes > self._max_total_scan_bytes:
                    reason = "byte_limit"
                    break
            if fnmatch.fnmatch(p.name, req.pattern):
                matches.append(str(p))

        return SearchFilesResponse(
            pattern=req.pattern, matches=matches, truncation_reason=reason
        )

    def _collect_grep_matches(
        self,
        base: Path,
        compiled: re.Pattern[str],
        file_pattern: str,
        max_matches: int,
    ) -> tuple[list[GrepMatch], bool, TruncationReason | None]:
        """Walk base recursively, match lines against compiled.

        Symlink entries are skipped before any stat() call (REQ-002). The scan is
        bounded by max_scanned_files, max_total_scan_bytes, and the traversal
        deadline; whichever limit stops the traversal is returned as the structured
        truncation reason (REQ-003).
        """
        matches: list[GrepMatch] = []
        reason: TruncationReason | None = None
        scanned_files = 0
        total_bytes = 0
        deadline = time.monotonic() + self._traversal_deadline_sec

        # PermissionError during rglob() traversal is swallowed by glob.py itself
        # (CPython v3.13+ Lib/glob.py: scandir() OSError caught in except OSError: pass).
        # See plans/20260817-161921_plan.md
        for p in sorted(base.rglob("*")):
            if len(matches) >= max_matches:
                return matches, True, reason
            if p.is_symlink():
                continue
            if time.monotonic() > deadline:
                reason = "deadline"
                break
            if not p.is_file() or not fnmatch.fnmatch(p.name, file_pattern):
                continue
            scanned_files += 1
            try:
                size = p.stat().st_size
            except OSError:
                continue
            total_bytes += size
            if scanned_files > self._max_scanned_files:
                reason = "scanned_file_limit"
                break
            if total_bytes > self._max_total_scan_bytes:
                reason = "byte_limit"
                break
            text = self._read_grep_text(p)
            if text is None:
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
                        return matches, True, reason
        return matches, False, reason

    @staticmethod
    def _read_grep_text(path: Path) -> str | None:
        """Read text from a file for grep. Returns None on decode/permission error."""
        try:
            return path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            return None

    def grep_files(self, req: GrepFilesRequest) -> GrepFilesResponse:
        """Search file contents under a directory using a regex pattern."""
        base = self._resolve_safe(req.path)
        self._require_dir(base, req.path)
        try:
            compiled = re.compile(req.pattern)
        except re.error as e:
            raise FileValidationError(f"Invalid regular expression: {e}")

        matches, truncated, reason = self._collect_grep_matches(
            base,
            compiled,
            req.file_pattern,
            req.max_matches,
        )
        return GrepFilesResponse(
            pattern=req.pattern,
            matches=matches,
            truncated=truncated,
            truncation_reason=reason,
        )

    def get_file_info(self, req: GetFileInfoRequest) -> GetFileInfoResponse:
        """Return metadata (size, timestamps, permissions) for a file or directory."""
        target = self._resolve_safe(req.path)
        if not target.exists():
            raise FileNotFoundError(f"Path does not exist: {req.path}")

        try:
            st = target.stat()
        except OSError as e:
            logger.error("get_file_info: stat failed for '%s': %s", target, e)
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
