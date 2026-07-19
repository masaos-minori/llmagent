#!/usr/bin/env python3
"""browser_mcp_models.py

Config loading, Pydantic models, and domain exceptions for browser-mcp.
"""

from __future__ import annotations

import dataclasses
import logging
from typing import Any

from pydantic import BaseModel, Field
from shared.config_loader import ConfigLoader

logger = logging.getLogger(__name__)


class BrowserAuthorizationError(RuntimeError):
    """Raised when a domain-allowlist check fails (HTTP 403)."""


class BrowserValidationError(ValueError):
    """Raised on invalid input (HTTP 400/422)."""


# ──────────────────────────────────────────────────────────────────────────────
# Typed config object
# ──────────────────────────────────────────────────────────────────────────────


@dataclasses.dataclass
class BrowserConfig:
    """Typed configuration for the Browser MCP server."""

    allowed_domains: list[str] = dataclasses.field(default_factory=list)
    max_response_kb: int = 256
    timeout_sec: int = 15
    auth_token: str = ""

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> BrowserConfig:
        """Construct from a raw config dict (e.g. loaded from TOML).

        Uses ``or`` for defaults to avoid str(None) producing "None" and
        int(None) raising TypeError when a key is present with a null value.
        """
        return cls(
            allowed_domains=list(d.get("allowed_domains") or []),
            max_response_kb=int(d.get("max_response_kb") or 256),
            timeout_sec=int(d.get("timeout_sec") or 15),
            auth_token=d.get("auth_token") or "",
        )

    @classmethod
    def load(cls) -> BrowserConfig:
        """Load from browser_mcp_server.toml; raises on failure (fail-fast)."""
        return cls.from_dict(ConfigLoader().load("browser_mcp_server.toml"))


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schema definitions (browser fetch)
# ──────────────────────────────────────────────────────────────────────────────


class BrowserFetchRequest(BaseModel):
    """Request body for a read-only browser fetch."""

    url: str = Field(
        ...,
        description="Target URL to fetch (must match the configured domain allowlist)",
    )
    max_response_kb: int | None = Field(
        default=None,
        ge=1,
        le=65536,
        description="Caller override for response size cap; clamped to the server max in service.py",
    )


class BrowserFetchResponse(BaseModel):
    """Response body from a browser fetch."""

    text: str
    truncated: bool
    url: str
    status_code: int
    elapsed_sec: float
