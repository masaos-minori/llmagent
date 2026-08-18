#!/usr/bin/env python3
"""scripts/mcp_servers/file/delete_models.py

Config loading and Pydantic request/response models for file-delete-mcp.
"""

from __future__ import annotations

import dataclasses
import logging
import os
from typing import Any, Self

from pydantic import BaseModel, ConfigDict, Field, model_validator
from shared.config_loader import ConfigLoader
from shared.config_utils import get_typed

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Typed config object
# ──────────────────────────────────────────────────────────────────────────────


@dataclasses.dataclass(frozen=True)
class FileDeleteConfig:
    """Typed configuration for the File Delete MCP server."""

    allowed_dirs: list[str] = dataclasses.field(default_factory=list)

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> FileDeleteConfig:
        """Construct from a raw config dict (e.g. loaded from TOML)."""
        return cls(
            allowed_dirs=list(get_typed(d, "allowed_dirs", list, "a list", default=[])),
        )

    @classmethod
    def load(cls) -> FileDeleteConfig:
        """Load from file_delete_mcp_server.toml; raises on failure (fail-fast)."""
        return cls.from_dict(ConfigLoader().load("file_delete_mcp_server.toml"))


# ──────────────────────────────────────────────────────────────────────────────
# Shared mixins
# ──────────────────────────────────────────────────────────────────────────────


class PathMixin(BaseModel):
    """Mixin providing shared path field with unified description."""

    path: str = Field(description="Absolute path of the target to delete")

    @model_validator(mode="after")
    def validate_path(self) -> Self:
        if not self.path:
            raise ValueError("path must not be empty")
        if not os.path.isabs(self.path):
            raise ValueError(f"path must be an absolute path, got: {self.path}")
        return self


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schema definitions
# ──────────────────────────────────────────────────────────────────────────────


class DeleteFileRequest(PathMixin):
    """Request model for deleting a single file."""

    model_config = ConfigDict(extra="forbid")

    dry_run: bool = Field(
        default=False,
        description="When true, return file info without deleting",
    )


class DeleteFileResponse(BaseModel):
    """Response indicating whether a file was deleted."""

    path: str
    deleted: bool
    file_info: str = ""


class DeleteDirectoryRequest(PathMixin):
    """Request model for deleting a directory."""

    model_config = ConfigDict(extra="forbid")

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
    """Response indicating whether a directory was deleted."""

    path: str
    deleted: bool
    dir_info: str = ""
