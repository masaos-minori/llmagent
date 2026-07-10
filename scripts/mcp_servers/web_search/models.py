#!/usr/bin/env python3
"""mcp_servers/web_search/models.py
Config loading, Pydantic models, and domain exceptions for web-search-mcp.
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


class WebSearchUpstreamError(RuntimeError):
    """Raised when all search providers fail."""


# ──────────────────────────────────────────────────────────────────────────────
# Typed config object
# ──────────────────────────────────────────────────────────────────────────────

# Defaults exposed for Pydantic Field constraints
DEFAULT_MAX_RESULTS: int = 5
MAX_RESULTS_LIMIT: int = 20


@dataclasses.dataclass
class WebSearchConfig:
    """Typed configuration for the Web Search MCP server."""

    default_max_results: int = DEFAULT_MAX_RESULTS
    max_results_limit: int = MAX_RESULTS_LIMIT

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> WebSearchConfig:
        """Construct from a raw config dict (e.g. loaded from TOML)."""
        return cls(
            default_max_results=int(d.get("default_max_results", DEFAULT_MAX_RESULTS)),
            max_results_limit=int(d.get("max_results_limit", MAX_RESULTS_LIMIT)),
        )

    @classmethod
    def load(cls) -> WebSearchConfig:
        """Load from web_search_mcp_server.toml; raises on failure (fail-fast)."""
        return cls.from_dict(ConfigLoader().load("web_search_mcp_server.toml"))


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schema definitions
# ──────────────────────────────────────────────────────────────────────────────


class SearchRequest(BaseModel):
    """Request schema for POST /search"""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query string",
    )
    max_results: int = Field(
        DEFAULT_MAX_RESULTS,
        ge=1,
        le=MAX_RESULTS_LIMIT,
        description="Maximum number of results to return (max 20)",
    )


class SearchResult(BaseModel):
    """Schema for a single search result item"""

    title: str
    url: str
    body: str
    provider: str  # Name of the provider that returned this result


class SearchResponse(BaseModel):
    """Response schema for POST /search"""

    query: str
    results: list[SearchResult]
    provider: str  # Name of the provider actually used
