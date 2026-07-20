#!/usr/bin/env python3
"""mcp_servers/web_search/service.py

Orchestration layer for web-search-mcp: builds/validates a `SearchRequest`,
calls `search_provider.search_duckduckgo`, measures latency, and updates
`health.py`/`metrics.py`.

This module is the sole caller of `health.record_success`/`record_failure`
and `metrics.record_query` in the web-search-mcp package. `web_search_server.py`
only *reads* their state (via `health.health_details()`/`is_degraded()` and
`metrics.snapshot()`) for the `/health` endpoint and no longer calls the
update hooks directly — see that module's `call_tool()` for the audit-logging
responsibility it retains instead.

Dependency direction: mcp_servers.web_search.service -> mcp_servers.web_search.{search_provider, health, metrics, web_search_models}, shared.formatters, shared.logger
Import from here: from mcp_servers.web_search.service import search_web
"""

from __future__ import annotations

import time
from typing import Any, cast

from shared.formatters import fmt_kvlog
from shared.logger import Logger

from mcp_servers.web_search import health, metrics
from mcp_servers.web_search.search_provider import (
    fetch_browser as _provider_fetch_browser,
)
from mcp_servers.web_search.search_provider import search_duckduckgo
from mcp_servers.web_search.web_search_models import (
    BrowserAuthorizationError,
    BrowserConfig,
    BrowserFetchRequest,
    BrowserFetchResponse,
    BrowserValidationError,
    SearchRequest,
    SearchResponse,
    SearchResult,
    WebSearchNetworkError,
    WebSearchParseError,
    WebSearchTimeoutError,
    WebSearchUpstreamError,
    _cfg,
)

logger = Logger(__name__, "/opt/llm/logs/web-search-mcp.log")


def _classify_upstream_error(exc: WebSearchUpstreamError) -> str:
    """Classify a raised WebSearchUpstreamError by its concrete subclass.

    Mirrors `web_search_server.py`'s own `_classify_upstream_error` (which the
    server keeps for its audit-log `error_type` field). Duplicated here rather
    than imported to avoid a `web_search_server -> formatters -> service ->
    web_search_server` import cycle.
    """
    if isinstance(exc, WebSearchTimeoutError):
        return "timeout"
    if isinstance(exc, WebSearchNetworkError):
        return "network_error"
    if isinstance(exc, WebSearchParseError):
        return "parse_error"
    return "provider_error"


async def search_web(args: dict[str, Any]) -> SearchResponse:
    """Execute a web search using DuckDuckGo, recording health/metrics.

    A zero-result search is a normal success (not a failure) and is recorded
    as such — `formatters.fdisp_search_web()` is responsible for turning an
    empty `SearchResponse.results` into a user-facing "no results" message.

    Raises:
        ValueError: if `args` fails `SearchRequest` validation (recorded as a
            "validation_error" metrics failure; not a provider-health failure,
            since it never reaches the provider).
        WebSearchUpstreamError: if the provider call fails (recorded as a
            classified metrics failure and a provider-health failure).
    """
    t0 = time.perf_counter()
    try:
        req = SearchRequest(**args)
        results = cast(
            list[SearchResult],
            await search_duckduckgo(
                req.query, req.max_results, _cfg.search_timeout_sec
            ),
        )
    except ValueError:
        ms = (time.perf_counter() - t0) * 1000
        metrics.record_query(
            success=False, latency_ms=ms, error_type="validation_error"
        )
        raise
    except WebSearchUpstreamError as e:
        ms = (time.perf_counter() - t0) * 1000
        error_type = _classify_upstream_error(e)
        metrics.record_query(success=False, latency_ms=ms, error_type=error_type)
        health.record_failure(error_type)
        raise

    ms = (time.perf_counter() - t0) * 1000
    logger.info(
        fmt_kvlog(
            "search",
            q=req.query[:80],
            provider="duckduckgo",
            n=len(results),
            ms=f"{ms:.0f}",
        ),
    )
    metrics.record_query(success=True, latency_ms=ms)
    health.record_success()
    return SearchResponse(
        query=req.query,
        results=results,
        provider="duckduckgo",
    )


def _classify_browser_error(exc: Exception) -> str:
    """Classify an exception raised while fetching a browser_fetch request.

    Mirrors `_classify_upstream_error`'s role for `search_web`, but keyed to
    the browser_fetch-specific exception hierarchy (BrowserAuthorizationError/
    BrowserValidationError) plus a catch-all for unclassified fetch failures
    (e.g. raw httpx exceptions propagating from search_provider.fetch_browser).
    """
    if isinstance(exc, BrowserAuthorizationError):
        return "authorization_error"
    if isinstance(exc, BrowserValidationError):
        return "validation_error"
    return "fetch_error"


async def fetch_browser(args: dict[str, Any]) -> BrowserFetchResponse:
    """Fetch a URL via browser_fetch, recording health/metrics independently of search_web.

    Raises:
        BrowserValidationError: if `args` fails `BrowserFetchRequest` validation,
            or the URL is malformed (recorded as a "validation_error" browser-metrics
            failure; not a browser-health failure, since it never reaches the fetch).
        BrowserAuthorizationError: if the target fails the domain-allowlist/
            IP-literal check (recorded as an "authorization_error" browser-metrics
            failure; not a browser-health failure either, for the same reason —
            it is a caller/target problem, not a signal that outbound fetches
            are failing).
        Exception: any other fetch failure propagating from the provider layer
            (recorded as a "fetch_error" browser-metrics AND browser-health
            failure — this is the only case that reflects the fetch itself
            failing).
    """
    t0 = time.perf_counter()
    browser_cfg = BrowserConfig.from_web_search_config(_cfg)
    try:
        req = BrowserFetchRequest(**args)
        result = await _provider_fetch_browser(req, browser_cfg)
    except (BrowserValidationError, BrowserAuthorizationError) as e:
        # Both are rejected before the outbound fetch is ever attempted (bad
        # input / disallowed target), so — mirroring search_web's ValueError
        # handling — they are recorded as metrics failures only, never a
        # provider-health failure.
        ms = (time.perf_counter() - t0) * 1000
        error_type = _classify_browser_error(e)
        metrics.record_browser_query(
            success=False, latency_ms=ms, error_type=error_type
        )
        raise
    except Exception as e:  # noqa: BLE001 — unclassified fetch failure, see UNK-01
        # A genuine fetch failure (e.g. an httpx network/timeout error from
        # search_provider.fetch_browser) is a provider-health signal.
        ms = (time.perf_counter() - t0) * 1000
        error_type = _classify_browser_error(e)
        metrics.record_browser_query(
            success=False, latency_ms=ms, error_type=error_type
        )
        health.record_browser_failure(error_type)
        raise

    ms = (time.perf_counter() - t0) * 1000
    logger.info(fmt_kvlog("browser_fetch", url=req.url[:80], ms=f"{ms:.0f}"))
    metrics.record_browser_query(success=True, latency_ms=ms)
    health.record_browser_success()
    return result
