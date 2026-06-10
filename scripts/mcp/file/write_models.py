#!/usr/bin/env python3
"""file_write_mcp_models.py
Config loading and Pydantic request/response models for file-write-mcp.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any

from pydantic import BaseModel, Field, field_validator
from shared.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Typed config object
# ──────────────────────────────────────────────────────────────────────────────


@dataclasses.dataclass
class FileWriteConfig:
    """Typed configuration for the File Write MCP server."""

    max_write_bytes: int = 1048576
    allowed_dirs: list[str] = dataclasses.field(default_factory=list)
    supported_extensions: list[str] = dataclasses.field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> FileWriteConfig:
        """Construct from a raw config dict (e.g. loaded from TOML)."""
        return cls(
            max_write_bytes=int(d.get("max_write_bytes", 1048576)),
            allowed_dirs=list(d.get("allowed_dirs", [])),
            supported_extensions=list(d.get("supported_extensions", [])),
        )

    @classmethod
    def load(cls) -> FileWriteConfig:
        """Load from file_write_mcp_server.toml; raises on failure (fail-fast)."""
        return cls.from_dict(ConfigLoader().load("file_write_mcp_server.toml"))


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schema definitions (write/create/move operations)
# ──────────────────────────────────────────────────────────────────────────────


class WriteFileRequest(BaseModel):
    path: str = Field(..., description="Absolute path of the file to write")
    content: str = Field(..., description="Content to write (UTF-8 text)")
    dry_run: bool = Field(
        default=False,
        description="When true, return diff without writing",
    )

    @field_validator("content")
    @classmethod
    def _check_content_bytes(cls, v: str) -> str:
        # Deferred import breaks the circular dependency:
        # file_write_mcp_models → file_write_mcp_service → file_write_mcp_models (avoided).
        # This validator runs only at validation time, not at import time.
        from mcp.file.write_service import (
            _service,  # noqa: PLC0415 — circular: write_models ↔ write_service
        )

        # len() returns character count, which may undercount the write limit
        # for multibyte characters. Check the byte limit after UTF-8 encoding.
        limit: int = _service._max_write_bytes
        if len(v.encode("utf-8")) > limit:
            raise ValueError(f"content exceeds {limit} bytes write limit")
        return v


class WriteFileResponse(BaseModel):
    path: str
    size: int
    applied: bool = True
    diff: str = ""


class EditOperation(BaseModel):
    """A single string replacement operation."""

    old_text: str = Field(..., description="String to replace (exact match)")
    new_text: str = Field(..., description="Replacement string")


class EditFileRequest(BaseModel):
    path: str = Field(..., description="Absolute path of the file to edit")
    edits: list[EditOperation] = Field(
        ...,
        description="List of replacement operations applied in order",
    )
    dry_run: bool = Field(
        default=False,
        description="When true, return only the diff without writing",
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
    dry_run: bool = Field(
        default=False,
        description="When true, return feasibility info without moving",
    )


class MoveFileResponse(BaseModel):
    source: str
    destination: str
    dry_run_info: str = ""
