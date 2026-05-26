#!/usr/bin/env python3
"""
file_read_mcp_models.py
Config loading and Pydantic request/response models for file-read-mcp.
"""

from __future__ import annotations

from config_loader import ConfigLoader
from logger import Logger
from pydantic import BaseModel, Field, model_validator

# Logger for config-load warnings; main log path is /opt/llm/logs/file-read-mcp.log
_models_logger = Logger(__name__, "/opt/llm/logs/file-read-mcp.log")

_cfg: dict | None = None


def _get_cfg() -> dict:
    """Load config on first call; cached for the module lifetime."""
    global _cfg
    if _cfg is None:
        try:
            _cfg = ConfigLoader().load("file_read_mcp_server.json")
        except Exception as e:
            _models_logger.warning(f"Config load failed: {e}")
            _cfg = {}
    return _cfg


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schema definitions (read-only operations)
# ──────────────────────────────────────────────────────────────────────────────


class FileEntry(BaseModel):
    name: str
    path: str
    type: str  # "file" or "dir"
    size: int


class ListDirectoryRequest(BaseModel):
    path: str = Field(..., description="Absolute path of the directory to list")


class ListDirectoryResponse(BaseModel):
    path: str
    entries: list[FileEntry]


class DirectoryTreeRequest(BaseModel):
    path: str = Field(..., description="Absolute path of the root directory")
    depth: int = Field(
        default=3,
        ge=1,
        description="Maximum recursion depth (capped by server configuration)",
    )


class TreeNode(BaseModel):
    name: str
    path: str
    type: str
    size: int
    children: list[TreeNode] = Field(default_factory=list)
    # True when this directory was not expanded because the depth limit was reached
    depth_limited: bool = False


class DirectoryTreeResponse(BaseModel):
    root: TreeNode


class ReadTextFileRequest(BaseModel):
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
        # head and tail are mutually exclusive; disallow both being set simultaneously
        if self.head is not None and self.tail is not None:
            raise ValueError("head and tail cannot be specified at the same time")
        return self


class ReadTextFileResponse(BaseModel):
    path: str
    content: str
    size: int


class ReadMediaFileRequest(BaseModel):
    path: str = Field(..., description="Absolute path of the media file to read")


class ReadMediaFileResponse(BaseModel):
    path: str
    content_base64: str  # base64-encoded file content
    mime_type: str  # MIME type (e.g. image/png)
    size: int


class ReadMultipleFilesRequest(BaseModel):
    paths: list[str] = Field(..., description="List of absolute file paths to read")


class FileResult(BaseModel):
    path: str
    content: str | None  # None means an error occurred; see the error field
    error: str | None = None
    size: int = 0


class ReadMultipleFilesResponse(BaseModel):
    results: list[FileResult]


class SearchFilesRequest(BaseModel):
    path: str = Field(..., description="Absolute path of the base directory to search")
    pattern: str = Field(..., description="Glob pattern (e.g. *.py, **/*.json)")


class SearchFilesResponse(BaseModel):
    pattern: str
    matches: list[str]


class GrepFilesRequest(BaseModel):
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
    file: str
    line_number: int
    line: str


class GrepFilesResponse(BaseModel):
    pattern: str
    matches: list[GrepMatch]
    truncated: bool  # true if results were cut off because max_matches was reached


class GetFileInfoRequest(BaseModel):
    path: str = Field(
        ..., description="Absolute path of the file or directory to inspect"
    )


class FileInfo(BaseModel):
    path: str
    name: str
    type: str  # "file" or "dir"
    size: int
    created_at: str  # ISO 8601 format
    modified_at: str  # ISO 8601 format
    permissions: str  # "rwxrwxrwx" format


class GetFileInfoResponse(BaseModel):
    info: FileInfo
