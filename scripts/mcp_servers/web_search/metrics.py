#!/usr/bin/env python3
"""scripts/mcp_servers/web_search/metrics.py

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


def _record(
    target: WebSearchMetrics, success: bool, latency_ms: float, error_type: str
) -> None:
    """Apply one query outcome to `target`'s counters and latency accumulator."""
    target.queries_total += 1
    target._latency_sum_ms += latency_ms
    if success:
        target.queries_succeeded += 1
        target.last_success_at = time.time()
    else:
        target.queries_failed += 1
        target.last_failure_at = time.time()
        target.last_error_type = error_type


def _snapshot(target: WebSearchMetrics) -> dict[str, object]:
    """Return a plain dict snapshot of `target`'s current metrics."""
    return {
        "queries_total": target.queries_total,
        "queries_succeeded": target.queries_succeeded,
        "queries_failed": target.queries_failed,
        "average_latency_ms": target.average_latency_ms,
        "last_success_at": target.last_success_at,
        "last_failure_at": target.last_failure_at,
        "last_error_type": target.last_error_type,
    }


def record_query(success: bool, latency_ms: float, error_type: str = "") -> None:
    """Record the outcome and latency of one query. Never accepts query text."""
    _record(_metrics, success, latency_ms, error_type)


def snapshot() -> dict[str, object]:
    """Return a plain dict snapshot of all current metrics."""
    return _snapshot(_metrics)


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
    _record(_browser_metrics, success, latency_ms, error_type)


def browser_snapshot() -> dict[str, object]:
    """Return a plain dict snapshot of all current browser_fetch metrics."""
    return _snapshot(_browser_metrics)


def reset_browser() -> None:
    """Reset browser_fetch metrics state to defaults. Test helper only."""
    global _browser_metrics
    _browser_metrics = WebSearchMetrics()
