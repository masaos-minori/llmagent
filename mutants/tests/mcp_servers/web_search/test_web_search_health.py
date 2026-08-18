"""tests/test_web_search_health.py

Unit tests for mcp_servers/web_search/health.py: pure in-memory provider
health-state tracking (no FastAPI/HTTP involvement), plus a small
HTTP-boundary check that `/health` folds `health.health_details()` in and
flips to 503 once `is_degraded()` is true.
"""

from __future__ import annotations

import time
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from mcp_servers.web_search import health, web_search_server


@pytest.fixture(autouse=True)
def _reset_health() -> Iterator[None]:
    """Reset both before AND after each test.

    health.py's ProviderHealth singletons are process-global, shared across
    every test file in the pytest session — a test that flips is_degraded()/
    is_browser_degraded() to True and only resets on entry (not on exit)
    leaks that degraded state into whatever test runs next (e.g.
    tests/test_mcp_server_health_status.py's "always healthy" assertion),
    which is order-dependent and can fail under pytest-randomly.
    """
    health.reset()
    health.reset_browser()
    yield
    health.reset()
    health.reset_browser()


class TestProviderHealth:
    def test_initial_state_not_degraded(self) -> None:
        assert health.is_degraded() is False
        assert health.health_details()["consecutive_failures"] == 0

    def test_provider_health_defaults(self) -> None:
        ph = health.ProviderHealth()
        assert ph.provider == "duckduckgo"
        assert ph.last_success_at is None
        assert ph.last_failure_at is None
        assert ph.last_error_type == ""
        assert ph.consecutive_failures == 0

    def test_record_success_sets_timestamp(self) -> None:
        before = time.time()
        health.record_success()
        after = time.time()

        last_success_at = health.health_details()["last_success_at"]
        assert isinstance(last_success_at, float)
        assert before <= last_success_at <= after

    def test_single_failure_not_yet_degraded(self) -> None:
        health.record_failure("timeout")

        assert health.is_degraded() is False
        assert health.health_details()["last_error_type"] == "timeout"

    def test_repeated_failures_flip_degraded(self) -> None:
        for _ in range(health.DEGRADED_THRESHOLD - 1):
            health.record_failure("network_error")
        assert health.is_degraded() is False

        health.record_failure("network_error")
        assert health.is_degraded() is True

    def test_success_after_failures_resets_degraded(self) -> None:
        for _ in range(health.DEGRADED_THRESHOLD):
            health.record_failure("provider_error")
        assert health.is_degraded() is True

        health.record_success()

        assert health.is_degraded() is False
        assert health.health_details()["consecutive_failures"] == 0

    def test_health_details_shape(self) -> None:
        details = health.health_details()

        assert set(details) == {
            "provider",
            "last_success_at",
            "last_failure_at",
            "last_error_type",
            "consecutive_failures",
            "degraded",
        }
        assert details["provider"] == "duckduckgo"
        assert isinstance(details["consecutive_failures"], int)
        assert isinstance(details["degraded"], bool)


class TestHealthEndpointWiring:
    def test_health_endpoint_reports_healthy_provider_details(self) -> None:
        client = TestClient(web_search_server.app)

        resp = client.get("/health")

        assert resp.status_code == 200
        data = resp.json()
        assert data["dependencies"] == {}
        assert data["details"]["provider"]["consecutive_failures"] == 0
        assert data["details"]["provider"]["degraded"] is False
        assert "metrics" in data["details"]

    def test_health_endpoint_degrades_after_repeated_failures(self) -> None:
        for _ in range(health.DEGRADED_THRESHOLD):
            health.record_failure("network_error")
        client = TestClient(web_search_server.app)

        resp = client.get("/health")

        assert resp.status_code == 503
        data = resp.json()
        assert "web_search_provider" in data["dependencies"]
        assert data["details"]["provider"]["degraded"] is True


class TestBrowserProviderHealth:
    """browser_fetch's health tracking is an independent singleton (UNK-03) —
    a browser_fetch failure streak must not flip search_web's own
    is_degraded(), and vice versa."""

    def test_initial_state_not_degraded(self) -> None:
        assert health.is_browser_degraded() is False
        assert health.browser_health_details()["consecutive_failures"] == 0

    def test_browser_provider_health_provider_name(self) -> None:
        assert health.browser_health_details()["provider"] == "browser_fetch"

    def test_record_browser_success_sets_timestamp(self) -> None:
        before = time.time()
        health.record_browser_success()
        after = time.time()

        last_success_at = health.browser_health_details()["last_success_at"]
        assert isinstance(last_success_at, float)
        assert before <= last_success_at <= after

    def test_repeated_browser_failures_flip_browser_degraded(self) -> None:
        for _ in range(health.DEGRADED_THRESHOLD - 1):
            health.record_browser_failure("fetch_error")
        assert health.is_browser_degraded() is False

        health.record_browser_failure("fetch_error")
        assert health.is_browser_degraded() is True

    def test_browser_failures_do_not_affect_search_web_degraded(self) -> None:
        for _ in range(health.DEGRADED_THRESHOLD):
            health.record_browser_failure("fetch_error")

        assert health.is_browser_degraded() is True
        assert health.is_degraded() is False

    def test_search_web_failures_do_not_affect_browser_degraded(self) -> None:
        for _ in range(health.DEGRADED_THRESHOLD):
            health.record_failure("network_error")

        assert health.is_degraded() is True
        assert health.is_browser_degraded() is False

    def test_browser_health_details_shape(self) -> None:
        details = health.browser_health_details()

        assert set(details) == {
            "provider",
            "last_success_at",
            "last_failure_at",
            "last_error_type",
            "consecutive_failures",
            "degraded",
        }


class TestBrowserHealthEndpointWiring:
    def test_health_endpoint_reports_browser_provider_details(self) -> None:
        client = TestClient(web_search_server.app)

        resp = client.get("/health")

        assert resp.status_code == 200
        data = resp.json()
        assert data["details"]["browser_provider"]["consecutive_failures"] == 0
        assert data["details"]["browser_provider"]["degraded"] is False
        assert "browser_metrics" in data["details"]

    def test_health_endpoint_degrades_after_repeated_browser_failures(self) -> None:
        for _ in range(health.DEGRADED_THRESHOLD):
            health.record_browser_failure("fetch_error")
        client = TestClient(web_search_server.app)

        resp = client.get("/health")

        assert resp.status_code == 503
        data = resp.json()
        assert "browser_fetch_provider" in data["dependencies"]
        assert data["details"]["browser_provider"]["degraded"] is True
        # search_web's own dependency key must not be present.
        assert "web_search_provider" not in data["dependencies"]
