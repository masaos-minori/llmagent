#!/usr/bin/env python3
"""mcp_servers/web_search/models.py

Config loading, Pydantic models, and domain exceptions for web-search-mcp.
"""

from __future__ import annotations

import dataclasses
import logging
import unicodedata
from typing import Any

from pydantic import BaseModel, Field, field_validator
from shared.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────────────────────
# Domain exceptions
# ──────────────────────────────────────────────────────────────────────────────


class WebSearchUpstreamError(RuntimeError):
    """Raised when all search providers fail."""


class WebSearchTimeoutError(WebSearchUpstreamError):
    """Raised when the provider call exceeds search_timeout_sec."""


class WebSearchNetworkError(WebSearchUpstreamError):
    """Raised on a network-level provider failure (connection, DNS, etc.)."""


class WebSearchProviderError(WebSearchUpstreamError):
    """Raised on a non-network provider-side failure."""


class WebSearchParseError(WebSearchUpstreamError):
    """Raised when provider response data cannot be parsed into SearchResult."""


# ──────────────────────────────────────────────────────────────────────────────
# Typed config object
# ──────────────────────────────────────────────────────────────────────────────

# Defaults exposed for Pydantic Field constraints
DEFAULT_MAX_RESULTS: int = 5
MAX_RESULTS_LIMIT: int = 20
# Safety ceiling on max_results_limit, independent of any configured value.
HARD_MAX_RESULTS_LIMIT: int = 100
# Safety ceiling on search_timeout_sec, independent of any configured value.
HARD_SEARCH_TIMEOUT_SEC_LIMIT: float = 60.0


@dataclasses.dataclass
class WebSearchConfig:
    """Typed configuration for the Web Search MCP server."""

    default_max_results: int = DEFAULT_MAX_RESULTS
    max_results_limit: int = MAX_RESULTS_LIMIT
    search_timeout_sec: float = 10.0

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> WebSearchConfig:
        """Construct from a raw config dict (e.g. loaded from TOML).

        Raises:
            ValueError: if any configured value violates its invariant.
        """
        default_max_results = int(d.get("default_max_results", DEFAULT_MAX_RESULTS))
        max_results_limit = int(d.get("max_results_limit", MAX_RESULTS_LIMIT))
        search_timeout_sec = float(d.get("search_timeout_sec", 10.0))

        if default_max_results < 1:
            raise ValueError(
                f"default_max_results ({default_max_results}) must be >= 1"
            )
        if max_results_limit < 1:
            raise ValueError(f"max_results_limit ({max_results_limit}) must be >= 1")
        if default_max_results > max_results_limit:
            raise ValueError(
                f"default_max_results ({default_max_results}) must not exceed "
                f"max_results_limit ({max_results_limit})"
            )
        if max_results_limit > HARD_MAX_RESULTS_LIMIT:
            raise ValueError(
                f"max_results_limit ({max_results_limit}) must not exceed "
                f"HARD_MAX_RESULTS_LIMIT ({HARD_MAX_RESULTS_LIMIT})"
            )
        if not (0 < search_timeout_sec <= HARD_SEARCH_TIMEOUT_SEC_LIMIT):
            raise ValueError(
                f"search_timeout_sec ({search_timeout_sec}) must be in (0, {HARD_SEARCH_TIMEOUT_SEC_LIMIT}]"
            )

        return cls(
            default_max_results=default_max_results,
            max_results_limit=max_results_limit,
            search_timeout_sec=search_timeout_sec,
        )

    @classmethod
    def load(cls) -> WebSearchConfig:
        """Load from web_search_mcp_server.toml; raises on failure (fail-fast)."""
        return cls.from_dict(ConfigLoader().load("web_search_mcp_server.toml"))


# ──────────────────────────────────────────────────────────────────────────────
# Pydantic schema definitions
# ──────────────────────────────────────────────────────────────────────────────

# Module-level singleton, mirroring server.py's own _cfg pattern. No circular
# import: server.py imports from models.py, not the reverse, so loading config
# here at module-import time is safe. Config is fail-fast-loaded once at
# process startup (not hot-reloaded per request), consistent with server.py.
_cfg: WebSearchConfig = WebSearchConfig.load()


def get_max_results_limit() -> int:
    """Public accessor for the live, TOML-loaded max_results_limit bound.

    Used by web_search_tools.py to keep the search_web tool's inputSchema
    numerically in sync with SearchRequest's runtime constraint, without
    reaching into the module-private _cfg singleton.
    """
    return _cfg.max_results_limit


class SearchRequest(BaseModel):
    """Request schema for POST /search"""

    query: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Search query string",
    )
    max_results: int = Field(
        _cfg.default_max_results,
        ge=1,
        le=_cfg.max_results_limit,
        description="Maximum number of results to return",
    )

    @field_validator("query")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        """Trim whitespace and reject empty-after-trim or control-character queries."""
        stripped = value.strip()
        if not stripped:
            raise ValueError("query must not be empty after trimming whitespace")
        if any(unicodedata.category(ch) == "Cc" for ch in stripped):
            raise ValueError("query must not contain control characters")
        return stripped


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
