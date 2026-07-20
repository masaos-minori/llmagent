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

import pytest
from mcp_servers.web_search import metrics

SAMPLE_QUERY = "distinctive_test_query_xyz123"


@pytest.fixture(autouse=True)
def _reset_metrics() -> None:
    metrics.reset()


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
