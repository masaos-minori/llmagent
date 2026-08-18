"""tests/test_web_search_metrics.py

Unit tests for mcp_servers/web_search/metrics.py: pure in-memory query
counters/latency tracking (no FastAPI/HTTP involvement).

Includes a belt-and-suspenders check that `snapshot()`'s output never
contains a distinctive sample query string, documenting-by-assertion that
`record_query()`'s signature makes it structurally impossible to store full
query text.
"""

from __future__ import annotations

import time
from collections.abc import Iterator

import pytest
from mcp_servers.web_search import metrics

SAMPLE_QUERY = "distinctive_test_query_xyz123"


@pytest.fixture(autouse=True)
def _reset_metrics() -> Iterator[None]:
    """Reset both before AND after each test — metrics.py's counters are
    process-global singletons shared across the whole pytest session; see
    test_web_search_health.py's `_reset_health` fixture for the rationale."""
    metrics.reset()
    metrics.reset_browser()
    yield
    metrics.reset()
    metrics.reset_browser()


class TestWebSearchMetrics:
    def test_initial_snapshot_all_zero(self) -> None:
        snap = metrics.snapshot()

        assert snap["queries_total"] == 0
        assert snap["queries_succeeded"] == 0
        assert snap["queries_failed"] == 0
        assert snap["average_latency_ms"] == 0.0
        assert snap["last_success_at"] is None
        assert snap["last_failure_at"] is None
        assert snap["last_error_type"] == ""

    def test_metrics_defaults(self) -> None:
        m = metrics.WebSearchMetrics()
        assert m.queries_total == 0
        assert m.queries_succeeded == 0
        assert m.queries_failed == 0
        assert m.average_latency_ms == 0.0
        assert m.last_success_at is None
        assert m.last_failure_at is None
        assert m.last_error_type == ""

    def test_record_success_updates_counters(self) -> None:
        before = time.time()
        metrics.record_query(success=True, latency_ms=120.0)
        after = time.time()

        snap = metrics.snapshot()
        assert snap["queries_total"] == 1
        assert snap["queries_succeeded"] == 1
        assert snap["queries_failed"] == 0
        assert snap["average_latency_ms"] == 120.0
        last_success_at = snap["last_success_at"]
        assert isinstance(last_success_at, float)
        assert before <= last_success_at <= after

    def test_record_failure_updates_counters(self) -> None:
        metrics.record_query(
            success=False, latency_ms=50.0, error_type="provider_error"
        )

        snap = metrics.snapshot()
        assert snap["queries_total"] == 1
        assert snap["queries_succeeded"] == 0
        assert snap["queries_failed"] == 1
        assert snap["last_error_type"] == "provider_error"
        assert snap["last_failure_at"] is not None

    def test_average_latency_across_multiple_queries(self) -> None:
        metrics.record_query(success=True, latency_ms=100.0)
        metrics.record_query(success=True, latency_ms=200.0)
        metrics.record_query(success=True, latency_ms=300.0)

        snap = metrics.snapshot()
        assert snap["queries_total"] == 3
        assert snap["average_latency_ms"] == 200.0

    def test_snapshot_never_contains_query_text(self) -> None:
        metrics.record_query(success=True, latency_ms=10.0)
        metrics.record_query(success=False, latency_ms=20.0, error_type="timeout")
        metrics.record_query(success=True, latency_ms=30.0)

        assert SAMPLE_QUERY not in str(metrics.snapshot())


class TestBrowserMetrics:
    """browser_fetch's metrics tracking is an independent singleton (UNK-03) —
    recording a browser_fetch outcome must not change search_web's own
    counters, and vice versa."""

    def test_initial_browser_snapshot_all_zero(self) -> None:
        snap = metrics.browser_snapshot()

        assert snap["queries_total"] == 0
        assert snap["queries_succeeded"] == 0
        assert snap["queries_failed"] == 0
        assert snap["average_latency_ms"] == 0.0

    def test_record_browser_success_updates_counters(self) -> None:
        metrics.record_browser_query(success=True, latency_ms=80.0)

        snap = metrics.browser_snapshot()
        assert snap["queries_total"] == 1
        assert snap["queries_succeeded"] == 1
        assert snap["average_latency_ms"] == 80.0

    def test_record_browser_failure_updates_counters(self) -> None:
        metrics.record_browser_query(
            success=False, latency_ms=40.0, error_type="fetch_error"
        )

        snap = metrics.browser_snapshot()
        assert snap["queries_failed"] == 1
        assert snap["last_error_type"] == "fetch_error"

    def test_record_browser_query_does_not_affect_search_web_metrics(self) -> None:
        metrics.record_browser_query(success=True, latency_ms=10.0)

        assert metrics.snapshot()["queries_total"] == 0

    def test_record_query_does_not_affect_browser_metrics(self) -> None:
        metrics.record_query(success=True, latency_ms=10.0)

        assert metrics.browser_snapshot()["queries_total"] == 0

    def test_browser_snapshot_never_contains_url_text(self) -> None:
        sample_url = "https://distinctive-test-url-xyz123.example/"
        metrics.record_browser_query(success=True, latency_ms=10.0)
        metrics.record_browser_query(
            success=False, latency_ms=20.0, error_type="fetch_error"
        )

        assert sample_url not in str(metrics.browser_snapshot())
