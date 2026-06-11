#!/usr/bin/env python3
"""mcp/sqlite/models.py
Config loading and Pydantic request/response models for sqlite-mcp.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any

from pydantic import BaseModel, Field
from shared.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Domain exceptions
# ──────────────────────────────────────────────────────────────────────────────


class SqliteServiceError(RuntimeError):
    """Raised on sqlite service failures (DB not in allowlist, connection error, etc.)."""


class SqliteValidationError(ValueError):
    """Raised on invalid input (non-SELECT statement, missing DB name, etc.)."""


# ──────────────────────────────────────────────────────────────────────────────
# Typed config object
# ──────────────────────────────────────────────────────────────────────────────


@dataclasses.dataclass
class SqliteConfig:
    """Typed configuration for the SQLite MCP server."""

    db_paths: dict[str, str] = dataclasses.field(default_factory=dict)
    db_allowlist: list[str] = dataclasses.field(default_factory=list)
    max_rows: int = 100
    timeout_sec: float = 30.0
    auth_token: str = ""

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> SqliteConfig:
        """Construct from a raw config dict (e.g. loaded from TOML)."""
        return cls(
            db_paths=dict(d.get("db_paths", {})),
            db_allowlist=list(d.get("db_allowlist", [])),
            max_rows=int(d.get("max_rows", 100)),
            timeout_sec=float(d.get("timeout_sec", 30.0)),
            auth_token=str(d.get("auth_token", "")),
        )

    @classmethod
    def load(cls) -> SqliteConfig:
        """Load from sqlite_mcp_server.toml; raises on failure (fail-fast)."""
        return cls.from_dict(ConfigLoader().load("sqlite_mcp_server.toml"))


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schema definitions
# ──────────────────────────────────────────────────────────────────────────────


class QueryRequest(BaseModel):
    """Request body for the query_sqlite tool."""

    db: str = Field(..., description="DB name (e.g., 'rag' or 'session')")
    sql: str = Field(..., min_length=1, description="SELECT query string")


class QueryResponse(BaseModel):
    """Structured response from a successful query_sqlite call."""

    columns: list[str] = Field(..., description="Column names in result order")
    rows: list[list[Any]] = Field(
        ...,
        description="Result rows; each inner list is one row",
    )
    row_count: int = Field(
        ...,
        description="Number of rows returned (may be less than total)",
    )
    truncated: bool = Field(..., description="True when max_rows limit was reached")
