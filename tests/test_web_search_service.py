"""tests/test_web_search_service.py

Unit tests for mcp_servers/web_search/service.py::search_web(): the
orchestration layer covering the success path, the zero-result path (a
normal success, not a failure — see formatters.py for the "no results" text),
the provider-timeout path, the provider-error path, and the request-validation
path, plus the health.py/metrics.py update side effects on each path.
`search_duckduckgo` is monkeypatched at the point service.py looks it up — no
real DuckDuckGo network calls.
"""

from __future__ import annotations

import pytest
from mcp_servers.web_search import health, metrics, service
from mcp_servers.web_search.web_search_models import (
    SearchResult,
    WebSearchNetworkError,
    WebSearchParseError,
    WebSearchProviderError,
    WebSearchTimeoutError,
    WebSearchUpstreamError,
)


@pytest.fixture(autouse=True)
def _reset_state() -> None:
    health.reset()
    metrics.reset()


class TestSearchWebSuccess:
    async def test_success_returns_results_and_records_success(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_results = [
            SearchResult(title="t", url="u", body="b", provider="duckduckgo")
        ]

        async def _fake(*args: object, **kwargs: object) -> list[SearchResult]:
            return fake_results

        monkeypatch.setattr("mcp_servers.web_search.service.search_duckduckgo", _fake)

        resp = await service.search_web({"query": "hello", "max_results": 5})

        assert resp.results == fake_results
        assert resp.provider == "duckduckgo"
        assert resp.query == "hello"

        snap = metrics.snapshot()
        assert snap["queries_total"] == 1
        assert snap["queries_succeeded"] == 1
        assert snap["queries_failed"] == 0

        assert health.is_degraded() is False
        details = health.health_details()
        assert details["last_success_at"] is not None
        assert details["consecutive_failures"] == 0


class TestSearchWebZeroResults:
    async def test_zero_results_is_a_success_not_a_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def _fake(*args: object, **kwargs: object) -> list[SearchResult]:
            return []

        monkeypatch.setattr("mcp_servers.web_search.service.search_duckduckgo", _fake)

        resp = await service.search_web({"query": "hello", "max_results": 5})

        assert resp.results == []
        snap = metrics.snapshot()
        assert snap["queries_succeeded"] == 1
        assert snap["queries_failed"] == 0
        assert health.is_degraded() is False


class TestSearchWebProviderTimeout:
    async def test_timeout_propagates_and_records_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def _raise(*args: object, **kwargs: object) -> list[SearchResult]:
            raise WebSearchTimeoutError("DuckDuckGo search timed out after 10.0s")

        monkeypatch.setattr("mcp_servers.web_search.service.search_duckduckgo", _raise)

        with pytest.raises(WebSearchTimeoutError):
            await service.search_web({"query": "hello", "max_results": 5})

        snap = metrics.snapshot()
        assert snap["queries_total"] == 1
        assert snap["queries_failed"] == 1
        assert snap["last_error_type"] == "timeout"

        details = health.health_details()
        assert details["last_error_type"] == "timeout"
        assert details["consecutive_failures"] == 1


class TestSearchWebProviderError:
    @pytest.mark.parametrize(
        ("exc_cls", "expected_error_type"),
        [
            (WebSearchNetworkError, "network_error"),
            (WebSearchParseError, "parse_error"),
            (WebSearchProviderError, "provider_error"),
        ],
    )
    async def test_provider_error_propagates_and_classifies(
        self,
        monkeypatch: pytest.MonkeyPatch,
        exc_cls: type[WebSearchUpstreamError],
        expected_error_type: str,
    ) -> None:
        async def _raise(*args: object, **kwargs: object) -> list[SearchResult]:
            raise exc_cls("boom")

        monkeypatch.setattr("mcp_servers.web_search.service.search_duckduckgo", _raise)

        with pytest.raises(exc_cls):
            await service.search_web({"query": "hello", "max_results": 5})

        snap = metrics.snapshot()
        assert snap["queries_failed"] == 1
        assert snap["last_error_type"] == expected_error_type

        details = health.health_details()
        assert details["last_error_type"] == expected_error_type
        assert details["consecutive_failures"] == 1

    async def test_repeated_provider_errors_flip_degraded(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def _raise(*args: object, **kwargs: object) -> list[SearchResult]:
            raise WebSearchProviderError("boom")

        monkeypatch.setattr("mcp_servers.web_search.service.search_duckduckgo", _raise)

        for _ in range(health.DEGRADED_THRESHOLD):
            with pytest.raises(WebSearchProviderError):
                await service.search_web({"query": "hello", "max_results": 5})

        assert health.is_degraded() is True
        assert metrics.snapshot()["queries_failed"] == health.DEGRADED_THRESHOLD


class TestSearchWebValidationError:
    async def test_empty_query_raises_value_error_and_records_validation_failure(
        self,
    ) -> None:
        with pytest.raises(ValueError):
            await service.search_web({"query": ""})

        snap = metrics.snapshot()
        assert snap["queries_total"] == 1
        assert snap["queries_failed"] == 1
        assert snap["last_error_type"] == "validation_error"

        # Validation errors never reach the provider, so they are not a
        # provider-health failure — health state stays untouched.
        details = health.health_details()
        assert details["consecutive_failures"] == 0
        assert details["last_failure_at"] is None

    async def test_success_after_validation_error_still_resets_nothing_unusual(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        with pytest.raises(ValueError):
            await service.search_web({"query": ""})

        fake_results = [
            SearchResult(title="t", url="u", body="b", provider="duckduckgo")
        ]

        async def _fake(*args: object, **kwargs: object) -> list[SearchResult]:
            return fake_results

        monkeypatch.setattr("mcp_servers.web_search.service.search_duckduckgo", _fake)

        resp = await service.search_web({"query": "hello"})

        assert resp.results == fake_results
        snap = metrics.snapshot()
        assert snap["queries_total"] == 2
        assert snap["queries_succeeded"] == 1
        assert snap["queries_failed"] == 1
