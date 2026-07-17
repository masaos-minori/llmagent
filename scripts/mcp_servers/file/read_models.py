#!/usr/bin/env python3
"""file_read_mcp_models.py

Config loading and Pydantic request/response models for file-read-mcp.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any

from pydantic import BaseModel, Field, model_validator
from shared.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Typed config object
# ──────────────────────────────────────────────────────────────────────────────


@dataclasses.dataclass
class FileReadConfig:
    """Typed configuration for the File Read MCP server."""

    max_file_size_kb: int = 1000
    allowed_dirs: list[str] = dataclasses.field(default_factory=list)
    max_depth: int = 5
    max_files_per_batch: int = 100

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> FileReadConfig:
        """Construct from a raw config dict (e.g. loaded from TOML)."""
        return cls(
            max_file_size_kb=int(d.get("max_read_bytes", 1024000)) // 1024,
            allowed_dirs=list(d.get("allowed_dirs", [])),
            max_depth=int(d.get("max_tree_depth", 5)),
            max_files_per_batch=int(d.get("max_search_results", 100)),
        )

    @classmethod
    def load(cls) -> FileReadConfig:
        """Load from file_read_mcp_server.toml; raises on failure (fail-fast)."""
        return cls.from_dict(ConfigLoader().load("file_read_mcp_server.toml"))


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schema definitions (read-only operations)
# ──────────────────────────────────────────────────────────────────────────────


class FileEntry(BaseModel):
    """A single file or directory entry returned by list_directory."""

    name: str
    path: str
    type: str  # "file" or "dir"
    size: int


class ListDirectoryRequest(BaseModel):
    """Request model for listing directory entries."""

    path: str = Field(..., description="Absolute path of the directory to list")


class ListDirectoryResponse(BaseModel):
    """Response containing a list of directory entries."""

    path: str
    entries: list[FileEntry]


class DirectoryTreeRequest(BaseModel):
    """Request model for building a directory tree structure."""

    path: str = Field(..., description="Absolute path of the root directory")
    depth: int = Field(
        default=3,
        ge=1,
        description="Maximum recursion depth (capped by server configuration)",
    )


class TreeNode(BaseModel):
    """A node in a directory tree with optional recursive children."""

    name: str
    path: str
    type: str
    size: int
    children: list[TreeNode] = Field(default_factory=list)
    # True when this directory was not expanded because the depth limit was reached
    depth_limited: bool = False


class DirectoryTreeResponse(BaseModel):
    """Response containing a recursive directory tree."""

    root: TreeNode


class ReadTextFileRequest(BaseModel):
    """Request model for reading a text file with optional head/tail filtering."""

    path: str = Field(..., description="Absolute path of the file to read")
    head: int | None = Field(
        default=None,
        ge=1,
        description="Return only the first N lines (mutually exclusive with tail)",
    )
    tail: int | None = Field(
        default=None,
        ge=1,
        description="Return only the last N lines (mutually exclusive with head)",
    )

    @model_validator(mode="after")
    def _check_head_tail_exclusive(self) -> ReadTextFileRequest:
        """Validate that head and tail are not both specified simultaneously."""
        # head and tail are mutually exclusive; disallow both being set simultaneously
        if self.head is not None and self.tail is not None:
            raise ValueError("head and tail cannot be specified at the same time")
        return self


class ReadTextFileResponse(BaseModel):
    """Response containing the text content of a file."""

    path: str
    content: str
    size: int


class ReadMediaFileRequest(BaseModel):
    """Request model for reading a binary/media file."""

    path: str = Field(..., description="Absolute path of the media file to read")


class ReadMediaFileResponse(BaseModel):
    """Response containing base64-encoded binary file content."""

    path: str
    content_base64: str  # base64-encoded file content
    mime_type: str  # MIME type (e.g. image/png)
    size: int


class ReadMultipleFilesRequest(BaseModel):
    """Request model for batch-reading multiple files."""

    paths: list[str] = Field(..., description="List of absolute file paths to read")


class FileResult(BaseModel):
    """Result of reading a single file from a multi-file read request."""

    path: str
    content: str | None  # None means an error occurred; see the error field
    error: str | None = None
    size: int = 0


class ReadMultipleFilesResponse(BaseModel):
    """Response containing results from reading multiple files."""

    results: list[FileResult]


class SearchFilesRequest(BaseModel):
    """Request model for searching files by glob pattern."""

    path: str = Field(..., description="Absolute path of the base directory to search")
    pattern: str = Field(..., description="Glob pattern (e.g. *.py, **/*.json)")


class SearchFilesResponse(BaseModel):
    """Response containing file paths matching a glob pattern."""

    pattern: str
    matches: list[str]


class GrepFilesRequest(BaseModel):
    """Request model for searching file contents by regex pattern."""

    path: str = Field(..., description="Absolute path of the base directory to search")
    pattern: str = Field(..., description="Search pattern (Python regular expression)")
    file_pattern: str = Field(
        default="*",
        description="Glob pattern for target files (default: all files)",
    )
    max_matches: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of matches to return",
    )


class GrepMatch(BaseModel):
    """A single grep match result with source location and matched text."""

    file: str
    line_number: int
    line: str


class GrepFilesResponse(BaseModel):
    """Response containing grep match results."""

    pattern: str
    matches: list[GrepMatch]
    truncated: bool  # true if results were cut off because max_matches was reached


class GetFileInfoRequest(BaseModel):
    """Request model for getting file metadata."""

    path: str = Field(
        ...,
        description="Absolute path of the file or directory to inspect",
    )


class FileInfo(BaseModel):
    """File metadata including path, size, timestamps, and permissions."""

    path: str
    name: str
    type: str  # "file" or "dir"
    size: int
    created_at: str  # ISO 8601 format
    modified_at: str  # ISO 8601 format
    permissions: str  # "rwxrwxrwx" format


class GetFileInfoResponse(BaseModel):
    """Response containing file metadata."""

    info: FileInfo
