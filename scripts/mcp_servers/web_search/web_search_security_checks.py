#!/usr/bin/env python3
"""scripts/mcp_servers/web_search/web_search_security_checks.py — Web Search config posture checks.

Self-validation layer for the Web Search MCP server (REQ-015). This module owns every
SecurityCheckResult the server reports about its own configuration:
  _numeric_checks: the four numeric invariants, in posture order
  _allowlist_check: browser_allowed_domains as NOT_APPLICABLE, WARNING, or OK
  _is_hostname_shape: the posture-time mirror of search_provider._check_domain()
  _result / _invariant_result: SecurityCheckResult construction
  validate_web_search_security: the ordered five-element list server.py reports

Extracted from web_search_models.py, whose declared scope is config loading, Pydantic
models, and domain exceptions. Every check is pure: no network call is issued, and each
message names a setting and its state rather than an allowlist entry.
"""

from __future__ import annotations

from shared.security.result_dto import (
    REASON_ALLOWLIST_INVALID,
    REASON_CONFIG_INVALID,
    REASON_NOT_APPLICABLE,
    REASON_OK,
    SecurityCheckResult,
    SecurityCheckStatus,
)

from mcp_servers.web_search.web_search_models import (
    HARD_BROWSER_MAX_RESPONSE_KB,
    HARD_BROWSER_TIMEOUT_SEC_LIMIT,
    HARD_MAX_RESULTS_LIMIT,
    HARD_SEARCH_TIMEOUT_SEC_LIMIT,
    WebSearchConfig,
)


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
    """Return True when *value* can match the hostname search_provider._check_domain() compares against.

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
