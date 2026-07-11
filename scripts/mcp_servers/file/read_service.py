#!/usr/bin/env python3
"""mcp_servers/file/read_service.py
ReadFileService dispatch formatters + lazy singleton proxy for file-read-mcp.

Split layout:
  read_business.py          — ReadFileService class (security wrappers + business ops)
  read_static_helpers.py    — Pure static helpers (tree, formatting, slicing)
  read_service.py           — Dispatch formatters + build_service factory

Dependency direction: read_service → read_business, read_static_helpers, read_models
Import from here:  from mcp_servers.file.read_service import ReadFileService, build_service
"""

from __future__ import annotations

import asyncio
import logging
from collections.abc import Awaitable, Callable
from pathlib import Path

from mcp_servers.file.read_business import ReadFileService as _ReadFileServiceCore
from mcp_servers.file.read_models import (
    DirectoryTreeRequest,
    FileReadConfig,
    GetFileInfoRequest,
    GrepFilesRequest,
    ListDirectoryRequest,
    ReadMediaFileRequest,
    ReadMultipleFilesRequest,
    ReadTextFileRequest,
    SearchFilesRequest,
)
from mcp_servers.file.read_static_helpers import (
    count_tree_nodes,
    fmt_dir_entries,
    fmt_tree_node,
    has_depth_limit,
)
from mcp_servers.server import ToolArgs

logger = logging.getLogger(__name__)


class ReadFileService(_ReadFileServiceCore):
    """ReadFileService: business ops + dispatch formatters for the LLM."""

    # ── Dispatch handlers: format service results as plain text for the LLM ──

    async def fmt_list_directory(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            self.list_dir_entries,
            ListDirectoryRequest(**args),
            include_dir_sizes=False,
        )
        formatted: str = fmt_dir_entries(result.entries)
        return formatted

    async def fmt_list_directory_with_sizes(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            self.list_dir_entries,
            ListDirectoryRequest(**args),
            include_dir_sizes=True,
        )
        formatted: str = fmt_dir_entries(result.entries)
        return formatted

    async def fmt_directory_tree(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            lambda: self.build_directory_tree(DirectoryTreeRequest(**args)),
        )
        effective_depth = min(args.get("depth", 3), self._max_tree_depth)
        total_nodes = count_tree_nodes(result.root)
        trunc_note = ", truncated" if has_depth_limit(result.root) else ""
        header = f"[Tree: {total_nodes} nodes, depth={effective_depth}{trunc_note}]\n"
        tree_text: str = header + fmt_tree_node(result.root)
        return tree_text

    async def fmt_read_text_file(self, args: ToolArgs) -> str:
        result = await asyncio.to_thread(
            lambda: self.read_text_file(ReadTextFileRequest(**args)),
        )
        content: str = result.content
        return content

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
        return "\n".join(parts) if parts else "(no files)"

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
