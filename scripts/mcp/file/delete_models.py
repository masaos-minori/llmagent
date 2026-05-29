#!/usr/bin/env python3
"""
file_delete_mcp_models.py
Config loading and Pydantic request/response models for file-delete-mcp.
"""

from __future__ import annotations

from pydantic import BaseModel, Field
from shared.config_loader import ConfigLoader
from shared.logger import Logger

# Logger for config-load warnings; main log path is /opt/llm/logs/file-delete-mcp.log
_models_logger = Logger(__name__, "/opt/llm/logs/file-delete-mcp.log")

_cfg: dict | None = None


def _get_cfg() -> dict:
    """Load config on first call; cached for the module lifetime."""
    global _cfg
    if _cfg is None:
        try:
            _cfg = ConfigLoader().load("file_delete_mcp_server.toml")
        except Exception as e:
            _models_logger.warning(f"Config load failed: {e}")
            _cfg = {}
    return _cfg


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schema definitions (delete operations only)
# ──────────────────────────────────────────────────────────────────────────────


class DeleteFileRequest(BaseModel):
    path: str = Field(..., description="Absolute path of the file to delete")
    dry_run: bool = Field(
        default=False, description="When true, return file info without deleting"
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
        default=False, description="When true, delete contents recursively"
    )
    dry_run: bool = Field(
        default=False, description="When true, return directory info without deleting"
    )


class DeleteDirectoryResponse(BaseModel):
    path: str
    deleted: bool
    dir_info: str = ""
