#!/usr/bin/env python3
"""mcp_servers/web_search/metrics.py

Lightweight, in-process query metrics for web-search-mcp.

Dependency direction: mcp_servers.web_search.metrics → (stdlib only, leaf module)
Import from here:  from mcp_servers.web_search import metrics

Tracks total/succeeded/failed query counts, average latency, and last
success/failure timestamps plus the last error type. No persistence across
restarts and no external metrics backend (Prometheus/OpenTelemetry) — purely
in-memory counters, single-process (see health.py's module docstring for the
single-worker justification, which applies identically here).

By construction, the public API never accepts a query string anywhere:
`record_query()` takes only `success`, `latency_ms`, and `error_type`, so it
is structurally impossible to record full query text through this module.
This invariant applies identically to `record_browser_query()` — it never
accepts a URL either.
"""

from __future__ import annotations

import dataclasses
import time


@dataclasses.dataclass
class WebSearchMetrics:
    """Mutable in-process query counters and latency accumulator."""

    queries_total: int = 0
    queries_succeeded: int = 0
    queries_failed: int = 0
    _latency_sum_ms: float = 0.0
    last_success_at: float | None = None
    last_failure_at: float | None = None
    last_error_type: str = ""

    @property
    def average_latency_ms(self) -> float:
        """Mean latency across all recorded queries, or 0.0 if none yet."""
        if self.queries_total == 0:
            return 0.0
        return self._latency_sum_ms / self.queries_total


_metrics = WebSearchMetrics()


def record_query(success: bool, latency_ms: float, error_type: str = "") -> None:
    """Record the outcome and latency of one query. Never accepts query text."""
    _metrics.queries_total += 1
    _metrics._latency_sum_ms += latency_ms
    if success:
        _metrics.queries_succeeded += 1
        _metrics.last_success_at = time.time()
    else:
        _metrics.queries_failed += 1
        _metrics.last_failure_at = time.time()
        _metrics.last_error_type = error_type


def snapshot() -> dict[str, object]:
    """Return a plain dict snapshot of all current metrics."""
    return {
        "queries_total": _metrics.queries_total,
        "queries_succeeded": _metrics.queries_succeeded,
        "queries_failed": _metrics.queries_failed,
        "average_latency_ms": _metrics.average_latency_ms,
        "last_success_at": _metrics.last_success_at,
        "last_failure_at": _metrics.last_failure_at,
        "last_error_type": _metrics.last_error_type,
    }


def reset() -> None:
    """Reset metrics state to defaults. Test helper only."""
    global _metrics
    _metrics = WebSearchMetrics()


# ──────────────────────────────────────────────────────────────────────────────
# browser_fetch metrics tracking (independent singleton, see UNK-03)
# ──────────────────────────────────────────────────────────────────────────────

_browser_metrics = WebSearchMetrics()


def record_browser_query(
    success: bool, latency_ms: float, error_type: str = ""
) -> None:
    """Record the outcome and latency of one browser_fetch call. Never accepts a URL."""
    _browser_metrics.queries_total += 1
    _browser_metrics._latency_sum_ms += latency_ms
    if success:
        _browser_metrics.queries_succeeded += 1
        _browser_metrics.last_success_at = time.time()
    else:
        _browser_metrics.queries_failed += 1
        _browser_metrics.last_failure_at = time.time()
        _browser_metrics.last_error_type = error_type


def browser_snapshot() -> dict[str, object]:
    """Return a plain dict snapshot of all current browser_fetch metrics."""
    return {
        "queries_total": _browser_metrics.queries_total,
        "queries_succeeded": _browser_metrics.queries_succeeded,
        "queries_failed": _browser_metrics.queries_failed,
        "average_latency_ms": _browser_metrics.average_latency_ms,
        "last_success_at": _browser_metrics.last_success_at,
        "last_failure_at": _browser_metrics.last_failure_at,
        "last_error_type": _browser_metrics.last_error_type,
    }


def reset_browser() -> None:
    """Reset browser_fetch metrics state to defaults. Test helper only."""
    global _browser_metrics
    _browser_metrics = WebSearchMetrics()
