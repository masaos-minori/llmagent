#!/usr/bin/env python3
"""
file_mcp_models.py
Config loading and Pydantic request/response models for file_mcp_server.

Dependency direction: file_mcp_models → (no local deps at module level)
Note: WriteFileRequest._check_content_bytes imports _service from
      file_mcp_service at call time (deferred import) to break the circular
      dependency that would arise from a top-level import.
"""

from config_loader import ConfigLoader
from logger import Logger
from pydantic import BaseModel, Field, field_validator, model_validator

# ──────────────────────────────────────────────────────────────────────────────
# Config loading (config/file_mcp_server.json)
# ──────────────────────────────────────────────────────────────────────────────
# Logger is defined here only for config-load warnings; the main log path lives
# in file_mcp_server.py (where Logger("/opt/llm/logs/file-mcp.log") is set).
_models_logger = Logger(__name__, "/opt/llm/logs/file-mcp.log")

_cfg: dict | None = None


def _get_cfg() -> dict:
    """Load config on first call; cached for the module lifetime."""
    global _cfg
    if _cfg is None:
        try:
            _cfg = ConfigLoader().load("file_mcp_server.json")
        except Exception as e:
            _models_logger.warning(f"Config load failed: {e}")
            _cfg = {}
    return _cfg


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schema definitions
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
    children: list["TreeNode"] = Field(default_factory=list)
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
    def _check_head_tail_exclusive(self) -> "ReadTextFileRequest":
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


class WriteFileRequest(BaseModel):
    path: str = Field(..., description="Absolute path of the file to write")
    content: str = Field(..., description="Content to write (UTF-8 text)")

    @field_validator("content")
    @classmethod
    def _check_content_bytes(cls, v: str) -> str:
        # Deferred import breaks the circular dependency:
        # file_mcp_models → file_mcp_service → file_mcp_models (avoided).
        # This validator runs only at validation time, not at import time.
        from file_mcp_service import _service  # noqa: PLC0415

        # len() returns character count, which may undercount the write limit
        # for multibyte characters. Check the byte limit after UTF-8 encoding.
        limit: int = _service._max_write_bytes
        if len(v.encode("utf-8")) > limit:
            raise ValueError(f"content exceeds {limit} bytes write limit")
        return v


class WriteFileResponse(BaseModel):
    path: str
    size: int


class EditOperation(BaseModel):
    """A single string replacement operation."""

    old_text: str = Field(..., description="String to replace (exact match)")
    new_text: str = Field(..., description="Replacement string")


class EditFileRequest(BaseModel):
    path: str = Field(..., description="Absolute path of the file to edit")
    edits: list[EditOperation] = Field(
        ..., description="List of replacement operations applied in order"
    )
    dry_run: bool = Field(
        default=False, description="When true, return only the diff without writing"
    )


class EditFileResponse(BaseModel):
    path: str
    diff: str  # diff text in unified diff format
    applied: bool  # true if the change was actually written to disk


class CreateDirectoryRequest(BaseModel):
    path: str = Field(
        ...,
        description="Absolute path of the directory to create"
        " (parent directories are created automatically)",
    )


class CreateDirectoryResponse(BaseModel):
    path: str
    created: bool  # true if newly created, false if it already existed


class MoveFileRequest(BaseModel):
    source: str = Field(..., description="Absolute path of the source")
    destination: str = Field(..., description="Absolute path of the destination")


class MoveFileResponse(BaseModel):
    source: str
    destination: str


class SearchFilesRequest(BaseModel):
    path: str = Field(..., description="Absolute path of the base directory to search")
    pattern: str = Field(..., description="Glob pattern (e.g. *.py, **/*.json)")


class SearchFilesResponse(BaseModel):
    pattern: str
    matches: list[str]


class DeleteFileRequest(BaseModel):
    path: str = Field(..., description="Absolute path of the file to delete")


class DeleteFileResponse(BaseModel):
    path: str
    deleted: bool


class DeleteDirectoryRequest(BaseModel):
    path: str = Field(..., description="Absolute path of the directory to delete")
    # recursive=True: remove contents recursively
    # False (default): only empty directories can be deleted
    recursive: bool = Field(
        default=False, description="When true, delete contents recursively"
    )


class DeleteDirectoryResponse(BaseModel):
    path: str
    deleted: bool


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
