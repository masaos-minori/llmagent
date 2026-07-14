#!/usr/bin/env python3
"""file_delete_mcp_models.py

Config loading and Pydantic request/response models for file-delete-mcp.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any

from pydantic import BaseModel, Field
from shared.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Typed config object
# ──────────────────────────────────────────────────────────────────────────────


@dataclasses.dataclass
class FileDeleteConfig:
    """Typed configuration for the File Delete MCP server."""

    allowed_dirs: list[str] = dataclasses.field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> FileDeleteConfig:
        """Construct from a raw config dict (e.g. loaded from TOML)."""
        return cls(
            allowed_dirs=list(d.get("allowed_dirs", [])),
        )

    @classmethod
    def load(cls) -> FileDeleteConfig:
        """Load from file_delete_mcp_server.toml; raises on failure (fail-fast)."""
        return cls.from_dict(ConfigLoader().load("file_delete_mcp_server.toml"))


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schema definitions
# ──────────────────────────────────────────────────────────────────────────────


class DeleteFileRequest(BaseModel):
    path: str = Field(..., description="Absolute path of the file to delete")
    dry_run: bool = Field(
        default=False,
        description="When true, return file info without deleting",
    )


class DeleteFileResponse(BaseModel):
    path: str
    deleted: bool
    file_info: str = ""


class DeleteDirectoryRequest(BaseModel):
    path: str = Field(..., description="Absolute path of the directory to delete")
    # recursive=True: remove contents recursively
    # False (default): only empty directories can be deleted
    recursive: bool = Field(
        default=False,
        description="When true, delete contents recursively",
    )
    dry_run: bool = Field(
        default=False,
        description="When true, return directory info without deleting",
    )


class DeleteDirectoryResponse(BaseModel):
    path: str
    deleted: bool
    dir_info: str = ""
