#!/usr/bin/env python3
"""scripts/mcp_servers/web_search/web_search_models.py

Config loading, Pydantic models, and domain exceptions for web-search-mcp.
"""

from __future__ import annotations

import dataclasses
import unicodedata
from typing import Any

from pydantic import BaseModel, Field, field_validator
from shared.config_loader import ConfigLoader
from shared.config_utils import get_str, get_typed

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


class BrowserAuthorizationError(RuntimeError):
    """Raised when a domain-allowlist check fails (HTTP 403)."""


class BrowserValidationError(ValueError):
    """Raised on invalid input (HTTP 400/422)."""


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
# Safety ceilings on the browser_fetch settings, mirroring the two ceilings above.
HARD_BROWSER_TIMEOUT_SEC_LIMIT: int = 120
HARD_BROWSER_MAX_RESPONSE_KB: int = 4096
# The one config file this server reads; the posture fingerprint names it (REQ-017).
WEB_SEARCH_OWN_CONFIG_FILE: str = "web_search_mcp_server.toml"


def _validate_config_bounds(
    default_max_results: int,
    max_results_limit: int,
    search_timeout_sec: float,
    browser_timeout_sec: int,
    browser_max_response_kb: int,
) -> None:
    """Enforce WebSearchConfig's numeric invariants.

    The tuple is the invariant list: one entry per rule, in the order the rules
    are reported. It covers every value `web_search_security_checks._numeric_checks()` reports on, so a
    configuration the posture would flag is rejected here at load instead of
    starting and then reporting a failed check.

    Raises:
        ValueError: if any value violates its invariant. Message text and
            check order match the pre-extraction inline checks exactly.
    """
    violations: tuple[tuple[bool, str], ...] = (
        (
            default_max_results < 1,
            f"default_max_results ({default_max_results}) must be >= 1",
        ),
        (
            max_results_limit < 1,
            f"max_results_limit ({max_results_limit}) must be >= 1",
        ),
        (
            default_max_results > max_results_limit,
            f"default_max_results ({default_max_results}) must not exceed "
            f"max_results_limit ({max_results_limit})",
        ),
        (
            max_results_limit > HARD_MAX_RESULTS_LIMIT,
            f"max_results_limit ({max_results_limit}) must not exceed "
            f"HARD_MAX_RESULTS_LIMIT ({HARD_MAX_RESULTS_LIMIT})",
        ),
        (
            not 0 < search_timeout_sec <= HARD_SEARCH_TIMEOUT_SEC_LIMIT,
            f"search_timeout_sec ({search_timeout_sec}) must be in "
            f"(0, {HARD_SEARCH_TIMEOUT_SEC_LIMIT}]",
        ),
        (
            not 0 < browser_timeout_sec <= HARD_BROWSER_TIMEOUT_SEC_LIMIT,
            f"browser_timeout_sec ({browser_timeout_sec}) must be in "
            f"(0, {HARD_BROWSER_TIMEOUT_SEC_LIMIT}]",
        ),
        (
            not 0 < browser_max_response_kb <= HARD_BROWSER_MAX_RESPONSE_KB,
            f"browser_max_response_kb ({browser_max_response_kb}) must be in "
            f"(0, {HARD_BROWSER_MAX_RESPONSE_KB}]",
        ),
    )
    for violated, message in violations:
        if violated:
            raise ValueError(message)


@dataclasses.dataclass
class WebSearchConfig:
    """Typed configuration for the Web Search MCP server."""

    default_max_results: int = DEFAULT_MAX_RESULTS
    max_results_limit: int = MAX_RESULTS_LIMIT
    search_timeout_sec: float = 10.0
    browser_allowed_domains: list[str] = dataclasses.field(default_factory=list)
    browser_max_response_kb: int = 256
    browser_timeout_sec: int = 15
    auth_token: str = ""

    def non_secret_view(self) -> dict[str, object]:
        """Return the config fields safe to hash into the posture fingerprint.

        Scalars, one list count, and one presence boolean: `auth_token` is a Secret and
        every `browser_allowed_domains` entry is an allowlist value, so neither is carried
        by value (REQ-002, REQ-009). A new dict is built instead of exposing the list.
        """
        return {
            "own_config_file": WEB_SEARCH_OWN_CONFIG_FILE,
            "default_max_results": self.default_max_results,
            "max_results_limit": self.max_results_limit,
            "search_timeout_sec": self.search_timeout_sec,
            "browser_max_response_kb": self.browser_max_response_kb,
            "browser_timeout_sec": self.browser_timeout_sec,
            "browser_allowlist_count": len(self.browser_allowed_domains),
            "auth_token_present": bool(self.auth_token),
        }

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> WebSearchConfig:
        """Construct from a raw config dict (e.g. loaded from TOML).

        Raises:
            ValueError: if any configured value violates its invariant, or if the
                removed ``browser_auth_token`` key is still present (fail closed
                instead of silently running without authentication).
        """
        if "browser_auth_token" in d:
            raise ValueError(
                "web_search_mcp_server.toml: 'browser_auth_token' was removed; "
                "use 'auth_token' (shared with config/agent.toml's "
                "[mcp_servers.web_search].auth_token)"
            )
        default_max_results = get_typed(
            d, "default_max_results", int, "an integer", default=DEFAULT_MAX_RESULTS
        )
        max_results_limit = get_typed(
            d, "max_results_limit", int, "an integer", default=MAX_RESULTS_LIMIT
        )
        search_timeout_sec = get_typed(
            d, "search_timeout_sec", float, "a float", default=10.0
        )
        browser_allowed_domains = list(
            get_typed(d, "browser_allowed_domains", list, "a list", default=[])
        )
        browser_max_response_kb = get_typed(
            d, "browser_max_response_kb", int, "an integer", default=256
        )  # noqa: PLR2004 — 256 KB default
        browser_timeout_sec = get_typed(
            d, "browser_timeout_sec", int, "an integer", default=15
        )  # noqa: PLR2004 — 15s default; 0 would cause instant timeout
        auth_token = get_str(d, "auth_token", "")

        _validate_config_bounds(
            default_max_results,
            max_results_limit,
            search_timeout_sec,
            browser_timeout_sec,
            browser_max_response_kb,
        )

        return cls(
            default_max_results=default_max_results,
            max_results_limit=max_results_limit,
            search_timeout_sec=search_timeout_sec,
            browser_allowed_domains=browser_allowed_domains,
            browser_max_response_kb=browser_max_response_kb,
            browser_timeout_sec=browser_timeout_sec,
            auth_token=auth_token,
        )

    @classmethod
    def load(cls) -> WebSearchConfig:
        """Load from web_search_mcp_server.toml; raises on failure (fail-fast)."""
        return cls.from_dict(ConfigLoader().load(WEB_SEARCH_OWN_CONFIG_FILE))


@dataclasses.dataclass
class BrowserConfig:
    """Thin sub-view of WebSearchConfig's browser_* fields for the browser_fetch tool."""

    allowed_domains: list[str]
    max_response_kb: int
    timeout_sec: int

    @classmethod
    def from_web_search_config(cls, cfg: WebSearchConfig) -> BrowserConfig:
        """Project the three browser_* fields out of a WebSearchConfig."""
        return cls(
            cfg.browser_allowed_domains,
            cfg.browser_max_response_kb,
            cfg.browser_timeout_sec,
        )


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
