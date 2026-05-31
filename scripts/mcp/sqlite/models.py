#!/usr/bin/env python3
"""
mcp/sqlite/models.py
Config loading and Pydantic request/response models for sqlite-mcp.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field
from shared.config_loader import ConfigLoader
from shared.logger import Logger

_models_logger = Logger(__name__, "/opt/llm/logs/sqlite-mcp.log")

_cfg: dict[str, Any] | None = None


def _get_cfg() -> dict[str, Any]:
    """Load config on first call; cached for the module lifetime."""
    global _cfg
    if _cfg is None:
        try:
            _cfg = ConfigLoader().load("sqlite_mcp_server.toml")
        except Exception as e:
            _models_logger.warning(f"Config load failed: {e}")
            _cfg = {}
    return _cfg


class QueryRequest(BaseModel):
    """Request body for the query_sqlite tool."""

    db: str = Field(..., description="DB name (e.g., 'rag' or 'session')")
    sql: str = Field(..., min_length=1, description="SELECT query string")


class QueryResponse(BaseModel):
    """Structured response from a successful query_sqlite call."""

    columns: list[str] = Field(..., description="Column names in result order")
    rows: list[list[Any]] = Field(
        ..., description="Result rows; each inner list is one row"
    )
    row_count: int = Field(
        ..., description="Number of rows returned (may be less than total)"
    )
    truncated: bool = Field(..., description="True when max_rows limit was reached")
