#!/usr/bin/env python3
"""
file_write_mcp_models.py
Config loading and Pydantic request/response models for file-write-mcp.
"""

from __future__ import annotations

from config_loader import ConfigLoader
from logger import Logger
from pydantic import BaseModel, Field, field_validator

# Logger for config-load warnings; main log path is /opt/llm/logs/file-write-mcp.log
_models_logger = Logger(__name__, "/opt/llm/logs/file-write-mcp.log")

_cfg: dict | None = None


def _get_cfg() -> dict:
    """Load config on first call; cached for the module lifetime."""
    global _cfg
    if _cfg is None:
        try:
            _cfg = ConfigLoader().load("file_write_mcp_server.json")
        except Exception as e:
            _models_logger.warning(f"Config load failed: {e}")
            _cfg = {}
    return _cfg


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schema definitions (write/create/move operations)
# ──────────────────────────────────────────────────────────────────────────────


class WriteFileRequest(BaseModel):
    path: str = Field(..., description="Absolute path of the file to write")
    content: str = Field(..., description="Content to write (UTF-8 text)")

    @field_validator("content")
    @classmethod
    def _check_content_bytes(cls, v: str) -> str:
        # Deferred import breaks the circular dependency:
        # file_write_mcp_models → file_write_mcp_service → file_write_mcp_models (avoided).
        # This validator runs only at validation time, not at import time.
        from file_write_mcp_service import _service  # noqa: PLC0415

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
