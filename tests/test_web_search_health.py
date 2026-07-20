"""tests/test_web_search_health.py

Unit tests for mcp_servers/web_search/health.py: pure in-memory provider
health-state tracking (no FastAPI/HTTP involvement), plus a small
HTTP-boundary check that `/health` folds `health.health_details()` in and
flips to 503 once `is_degraded()` is true.
"""

from __future__ import annotations

import time

import pytest
from fastapi.testclient import TestClient
from mcp_servers.web_search import health, web_search_server


@pytest.fixture(autouse=True)
def _reset_health() -> None:
    health.reset()


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
