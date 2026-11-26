"""tests/test_web_search_service.py

Unit tests for mcp_servers/web_search/web_search_service.py::search_web(): the
orchestration layer covering the success path, the zero-result path (a
normal success, not a failure — see formatters.py for the "no results" text),
the provider-timeout path, the provider-error path, and the request-validation
path, plus the health.py/metrics.py update side effects on each path.
`search_duckduckgo` is monkeypatched at the point service.py looks it up — no
real DuckDuckGo network calls.
"""

from __future__ import annotations

from collections.abc import Iterator

import httpx
import pytest
from mcp_servers.web_search import health, metrics, service
from mcp_servers.web_search.web_search_models import (
    BrowserAuthorizationError,
    BrowserFetchResponse,
    BrowserHttpStatusError,
    BrowserUnsupportedContentError,
    BrowserValidationError,
    SearchResult,
    WebSearchNetworkError,
    WebSearchParseError,
    WebSearchProviderError,
    WebSearchTimeoutError,
    WebSearchUpstreamError,
)


@pytest.fixture(autouse=True)
def _reset_state() -> Iterator[None]:
    """Reset both before AND after each test — health.py/metrics.py's
    singletons are process-global, shared across the whole pytest session;
    see test_web_search_health.py's `_reset_health` fixture for the
    rationale (a degraded-flipping test here must not leak state into an
    unrelated test elsewhere, e.g. test_mcp_server_health_status.py)."""
    health.reset()
    metrics.reset()
    health.reset_browser()
    metrics.reset_browser()
    yield
    health.reset()
    metrics.reset()
    health.reset_browser()
    metrics.reset_browser()


class TestSearchWebSuccess:
    async def test_success_returns_results_and_records_success(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        fake_results = [
            SearchResult(title="t", url="u", body="b", provider="duckduckgo")
        ]

        async def _fake(*args: object, **kwargs: object) -> list[SearchResult]:
            return fake_results

        monkeypatch.setattr(
            "mcp_servers.web_search.web_search_service.search_duckduckgo", _fake
        )

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

        monkeypatch.setattr(
            "mcp_servers.web_search.web_search_service.search_duckduckgo", _fake
        )

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

        monkeypatch.setattr(
            "mcp_servers.web_search.web_search_service.search_duckduckgo", _raise
        )

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

        monkeypatch.setattr(
            "mcp_servers.web_search.web_search_service.search_duckduckgo", _raise
        )

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

        monkeypatch.setattr(
            "mcp_servers.web_search.web_search_service.search_duckduckgo", _raise
        )

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

        monkeypatch.setattr(
            "mcp_servers.web_search.web_search_service.search_duckduckgo", _fake
        )

        resp = await service.search_web({"query": "hello"})

        assert resp.results == fake_results
        snap = metrics.snapshot()
        assert snap["queries_total"] == 2
        assert snap["queries_succeeded"] == 1
        assert snap["queries_failed"] == 1


class TestFetchBrowserSuccess:
    async def test_success_returns_result_and_records_browser_success(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def _ok(*args: object, **kwargs: object) -> BrowserFetchResponse:
            return BrowserFetchResponse(
                text="Hello",
                truncated=False,
                url="https://example.com/",
                status_code=200,
                elapsed_sec=0.01,
            )

        monkeypatch.setattr(
            "mcp_servers.web_search.web_search_service._provider_fetch_browser", _ok
        )
        # search_web's own health/metrics must stay untouched by a browser_fetch call.
        result = await service.fetch_browser({"url": "https://example.com/"})

        assert result.status_code == 200
        assert "Hello" in result.text

        browser_snap = metrics.browser_snapshot()
        assert browser_snap["queries_total"] == 1
        assert browser_snap["queries_succeeded"] == 1
        assert browser_snap["queries_failed"] == 0

        assert health.is_browser_degraded() is False
        assert health.browser_health_details()["last_success_at"] is not None

        # search_web's own state stays at its defaults.
        assert metrics.snapshot()["queries_total"] == 0
        assert health.is_degraded() is False


class TestFetchBrowserValidationError:
    async def test_bad_scheme_raises_and_records_validation_failure_only(self) -> None:
        with pytest.raises(BrowserValidationError):
            await service.fetch_browser({"url": "ftp://example.com/"})

        browser_snap = metrics.browser_snapshot()
        assert browser_snap["queries_failed"] == 1
        assert browser_snap["last_error_type"] == "validation_error"

        # Validation errors never reach the fetch, so they are not a
        # browser-health failure — health state stays untouched.
        details = health.browser_health_details()
        assert details["consecutive_failures"] == 0
        assert details["last_failure_at"] is None


class TestFetchBrowserAuthorizationError:
    async def test_disallowed_domain_raises_and_records_authorization_failure_only(
        self,
    ) -> None:
        with pytest.raises(BrowserAuthorizationError):
            await service.fetch_browser({"url": "https://not-allowed.example/"})

        browser_snap = metrics.browser_snapshot()
        assert browser_snap["queries_failed"] == 1
        assert browser_snap["last_error_type"] == "authorization_error"

        # An authorization rejection is a caller/target problem, not a signal
        # that outbound fetches are failing — not a browser-health failure.
        details = health.browser_health_details()
        assert details["consecutive_failures"] == 0
        assert details["last_failure_at"] is None


class TestFetchBrowserFetchError:
    async def test_unclassified_fetch_failure_records_metrics_and_health(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def _raise(*args: object, **kwargs: object) -> None:
            raise httpx.ConnectError("boom")

        monkeypatch.setattr(
            "mcp_servers.web_search.web_search_service._provider_fetch_browser", _raise
        )
        # Allow the request past _check_domain by not exercising it at all
        # (the provider is fully monkeypatched, so allowlist state is moot).
        with pytest.raises(httpx.ConnectError):
            await service.fetch_browser({"url": "https://example.com/"})

        browser_snap = metrics.browser_snapshot()
        assert browser_snap["queries_failed"] == 1
        assert browser_snap["last_error_type"] == "fetch_error"

        details = health.browser_health_details()
        assert details["last_error_type"] == "fetch_error"
        assert details["consecutive_failures"] == 1

    async def test_repeated_fetch_failures_flip_browser_degraded_only(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def _raise(*args: object, **kwargs: object) -> None:
            raise httpx.ConnectError("boom")

        monkeypatch.setattr(
            "mcp_servers.web_search.web_search_service._provider_fetch_browser", _raise
        )

        for _ in range(health.DEGRADED_THRESHOLD):
            with pytest.raises(httpx.ConnectError):
                await service.fetch_browser({"url": "https://example.com/"})

        assert health.is_browser_degraded() is True
        # search_web's own degradation state is unaffected by browser_fetch failures.
        assert health.is_degraded() is False


class TestFetchBrowserClassification:
    """Each fetch outcome is typed for metrics; only some count as health failures."""

    @staticmethod
    async def _fail_with(monkeypatch: pytest.MonkeyPatch, exc: Exception) -> None:
        async def _raise(*args: object, **kwargs: object) -> None:
            raise exc

        monkeypatch.setattr(
            "mcp_servers.web_search.web_search_service._provider_fetch_browser", _raise
        )
        with pytest.raises(type(exc)):
            await service.fetch_browser({"url": "https://example.com/"})

    @pytest.mark.parametrize(
        ("exc", "error_type", "is_health_failure"),
        [
            (BrowserHttpStatusError("x", 301, "redirect"), "http_redirect", False),
            (
                BrowserHttpStatusError("x", 404, "client_error"),
                "http_client_error",
                False,
            ),
            (
                BrowserHttpStatusError("x", 403, "client_error"),
                "http_client_error",
                False,
            ),
            (
                BrowserHttpStatusError("x", 429, "rate_limited"),
                "http_rate_limited",
                True,
            ),
            (
                BrowserHttpStatusError("x", 500, "server_error"),
                "http_server_error",
                True,
            ),
            (
                BrowserHttpStatusError("x", 503, "server_error"),
                "http_server_error",
                True,
            ),
            (BrowserHttpStatusError("x", 199, "other"), "http_other", True),
            (
                BrowserUnsupportedContentError("x", "application/pdf"),
                "unsupported_content",
                False,
            ),
            (WebSearchNetworkError("no such host"), "network_error", True),
            (httpx.ReadTimeout("slow"), "fetch_error", True),
            (httpx.ConnectError("refused"), "fetch_error", True),
        ],
    )
    async def test_error_type_and_health_effect(
        self,
        monkeypatch: pytest.MonkeyPatch,
        exc: Exception,
        error_type: str,
        is_health_failure: bool,
    ) -> None:
        await self._fail_with(monkeypatch, exc)

        assert metrics.browser_snapshot()["last_error_type"] == error_type
        assert metrics.browser_snapshot()["queries_failed"] == 1
        details = health.browser_health_details()
        assert details["consecutive_failures"] == (1 if is_health_failure else 0)
        assert health.is_degraded() is False

    async def test_a_success_records_no_failure(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        async def _ok(*args: object, **kwargs: object) -> BrowserFetchResponse:
            return BrowserFetchResponse(
                text="t", truncated=False, url="u", status_code=200, elapsed_sec=0.0
            )

        monkeypatch.setattr(
            "mcp_servers.web_search.web_search_service._provider_fetch_browser", _ok
        )
        await service.fetch_browser({"url": "https://example.com/"})

        assert metrics.browser_snapshot()["queries_failed"] == 0
        assert metrics.browser_snapshot()["last_error_type"] == ""
        assert health.browser_health_details()["consecutive_failures"] == 0
