#!/usr/bin/env python3
"""scripts/mcp_servers/web_search/web_search_models.py

Config loading, Pydantic models, and domain exceptions for web-search-mcp.
"""

from __future__ import annotations

import dataclasses
import logging
import unicodedata
from typing import Any

from pydantic import BaseModel, Field, field_validator
from shared.config_loader import ConfigLoader
from shared.config_utils import get_str, get_typed
from shared.security.result_dto import (
    REASON_ALLOWLIST_INVALID,
    REASON_CONFIG_INVALID,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)

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
    default_max_results: int, max_results_limit: int, search_timeout_sec: float
) -> None:
    """Enforce WebSearchConfig's numeric invariants.

    Raises:
        ValueError: if any value violates its invariant. Message text and
            check order match the pre-extraction inline checks exactly.
    """
    if default_max_results < 1:
        raise ValueError(f"default_max_results ({default_max_results}) must be >= 1")
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
            default_max_results, max_results_limit, search_timeout_sec
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
# Security posture validation (REQ-015)
# ──────────────────────────────────────────────────────────────────────────────


def _result(
    check_id: str,
    status: SecurityCheckStatus,
    reason_code: str,
    message: str,
) -> SecurityCheckResult:
    """One posture check result carrying the shared default versions."""
    return SecurityCheckResult(
        check_id=check_id,
        status=status,
        reason_code=reason_code,
        message=message,
    )


def _is_hostname_shape(value: str) -> bool:
    """Return True when *value* can match the hostname _check_domain() compares against.

    _check_domain() lowercases the URL hostname and compares it verbatim to the allowlist
    set, so an entry that keeps a scheme, a path, a port, whitespace, or an uppercase
    character can never match. This is a posture-time shape test only: _check_domain()
    stays the runtime authority.
    """
    if not value:
        return False
    if value != value.lower():
        return False
    return not any(char in value for char in " \t:/")


def _invariant_result(
    check_id: str,
    ok: bool,
    ok_message: str,
    fail_message: str,
) -> SecurityCheckResult:
    """Map one boolean invariant to its OK or FAILED posture result."""
    return _result(
        check_id,
        SecurityCheckStatus.OK if ok else SecurityCheckStatus.FAILED,
        REASON_OK if ok else REASON_CONFIG_INVALID,
        ok_message if ok else fail_message,
    )


def _numeric_checks(cfg: WebSearchConfig) -> list[SecurityCheckResult]:
    """The four numeric invariants, in the order the posture contract expects.

    Each entry pairs its condition with both message variants, so a check reports its
    state without naming the configured value.
    """
    return [
        _invariant_result(
            "server.results_bounds",
            cfg.default_max_results >= 1
            and cfg.max_results_limit >= 1
            and cfg.default_max_results <= cfg.max_results_limit
            and cfg.max_results_limit <= HARD_MAX_RESULTS_LIMIT,
            "default_max_results is within max_results_limit and the module ceiling",
            "result-count bounds are violated so the advertised inputSchema is not enforced",
        ),
        _invariant_result(
            "server.search_timeout_valid",
            0 < cfg.search_timeout_sec <= HARD_SEARCH_TIMEOUT_SEC_LIMIT,
            "search_timeout_sec is in (0, HARD_SEARCH_TIMEOUT_SEC_LIMIT]",
            "search_timeout_sec is outside (0, HARD_SEARCH_TIMEOUT_SEC_LIMIT]",
        ),
        _invariant_result(
            "server.browser_timeout_valid",
            0 < cfg.browser_timeout_sec <= HARD_BROWSER_TIMEOUT_SEC_LIMIT,
            "browser_timeout_sec is in (0, HARD_BROWSER_TIMEOUT_SEC_LIMIT]",
            "browser_timeout_sec must be positive and within "
            "HARD_BROWSER_TIMEOUT_SEC_LIMIT",
        ),
        _invariant_result(
            "server.browser_response_limit",
            0 < cfg.browser_max_response_kb <= HARD_BROWSER_MAX_RESPONSE_KB,
            "browser_max_response_kb is positive and within "
            "HARD_BROWSER_MAX_RESPONSE_KB",
            "browser_max_response_kb must be positive and within "
            "HARD_BROWSER_MAX_RESPONSE_KB",
        ),
    ]


def _allowlist_check(cfg: WebSearchConfig) -> SecurityCheckResult:
    """Map browser_allowed_domains to its posture result.

    An empty allowlist is NOT_APPLICABLE rather than FAILED: it removes the
    browser_fetch capability instead of widening a boundary, so the shipped deny-all
    configuration stays startable. A malformed entry is WARNING because the runtime
    already denies everything it cannot match.
    """
    entries = cfg.browser_allowed_domains
    if not entries:
        return _result(
            "server.browser_allowlist",
            SecurityCheckStatus.NOT_APPLICABLE,
            REASON_NOT_APPLICABLE,
            "browser_allowed_domains is empty so browser_fetch is disabled for every domain",
        )
    malformed = sum(1 for entry in entries if not _is_hostname_shape(entry))
    if malformed:
        return _result(
            "server.browser_allowlist",
            SecurityCheckStatus.WARNING,
            REASON_ALLOWLIST_INVALID,
            f"browser_allowed_domains contains {malformed} of "
            f"{len(entries)} entries that cannot match a hostname",
        )
    return _result(
        "server.browser_allowlist",
        SecurityCheckStatus.OK,
        REASON_OK,
        f"browser_allowed_domains holds {len(entries)} hostname-shaped entries",
    )


def validate_web_search_security(cfg: WebSearchConfig) -> list[SecurityCheckResult]:
    """Web Search's own configuration checks, in the order the posture contract expects.

    Pure function of the passed config: no network call is issued, so validation cannot
    reach the search provider or fetch a page. The five check ids are always present, with
    not_applicable used instead of omitting a check.

    server.browser_allowlist is the one id that is not FAILED on an empty list: an empty
    browser_allowed_domains removes the browser_fetch capability rather than widening a
    boundary, so the shipped deny-all configuration stays startable. A malformed entry is
    WARNING because the runtime already denies everything it cannot match.

    Messages name the setting and its state: allowlist entries are reported by count only.
    """
    checks = _numeric_checks(cfg)
    checks.append(_allowlist_check(cfg))
    return checks


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
