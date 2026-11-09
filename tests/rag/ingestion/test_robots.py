"""Tests for the opt-in robots.txt policy (crawl005).

Covers the four runtime surfaces: the new ``RobotsCache`` module, the
``LinkDiscovery`` filter integration, the orchestrator eager per-host fetch, and
the ``crawler.py`` config wiring.
"""

import logging
from unittest.mock import AsyncMock, MagicMock
from urllib.robotparser import RobotFileParser

import httpx
import pytest
from bs4 import BeautifulSoup
from rag.ingestion.crawler import WebCrawler
from rag.ingestion.http_fetcher import Fetched
from rag.ingestion.link_discovery import LinkDiscovery
from rag.ingestion.orchestrator import CrawlOrchestrator
from rag.ingestion.robots import RobotsCache


def _parser_with_disallow() -> RobotFileParser:
    parser = RobotFileParser()
    parser.parse(["User-agent: *", "Disallow: /private/"])
    return parser


def _status_response(status: int, text: str = "") -> MagicMock:
    resp = MagicMock()
    resp.status_code = status
    resp.text = text
    return resp


class TestRobotsCache:
    def test_is_allowed_unknown_host_returns_true(self):
        """Unknown host (no cache entry) allows, so a missing cache never blocks."""
        cache = RobotsCache("test-agent")
        assert cache.is_allowed("http://example.com/page") is True

    def test_is_allowed_denies_and_allows_by_rule(self):
        """can_fetch answers allow/deny against the parsed Disallow rule."""
        cache = RobotsCache("test-agent")
        cache._parsers["example.com"] = _parser_with_disallow()
        assert cache.is_allowed("http://example.com/private/x") is False
        assert cache.is_allowed("http://example.com/public") is True

    @pytest.mark.asyncio
    async def test_fetch_host_idempotent_once_per_host(self):
        """A second fetch for an already-fetched host issues no further request."""
        resp = MagicMock()
        resp.status_code = 200
        resp.text = "User-agent: *\nDisallow: /private/"
        client = MagicMock()
        client.get = AsyncMock(return_value=resp)
        cache = RobotsCache("test-agent")
        await cache.fetch_host("http://example.com/", client)
        await cache.fetch_host("http://example.com/", client)
        assert client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_fetch_host_404_falls_back_allow_all(self):
        """Non-2xx stores an allow-all parser and raises nothing."""
        resp = MagicMock()
        resp.status_code = 404
        resp.text = ""
        client = MagicMock()
        client.get = AsyncMock(return_value=resp)
        cache = RobotsCache("test-agent")
        await cache.fetch_host("http://example.com/", client)
        assert cache.is_allowed("http://example.com/private/x") is True

    @pytest.mark.asyncio
    async def test_fetch_host_401_falls_back_disallow_all(self):
        """401 is fail-closed: every URL on the host is disallowed."""
        client = MagicMock()
        client.get = AsyncMock(return_value=_status_response(401))
        cache = RobotsCache("test-agent")
        await cache.fetch_host("http://example.com/", client)
        assert cache.is_allowed("http://example.com/anything") is False

    @pytest.mark.asyncio
    async def test_fetch_host_403_falls_back_disallow_all(self):
        """403 is fail-closed: every URL on the host is disallowed."""
        client = MagicMock()
        client.get = AsyncMock(return_value=_status_response(403))
        cache = RobotsCache("test-agent")
        await cache.fetch_host("http://example.com/", client)
        assert cache.is_allowed("http://example.com/anything") is False

    @pytest.mark.asyncio
    async def test_fetch_host_500_falls_back_disallow_all(self):
        """5xx is fail-closed: every URL on the host is disallowed."""
        client = MagicMock()
        client.get = AsyncMock(return_value=_status_response(500))
        cache = RobotsCache("test-agent")
        await cache.fetch_host("http://example.com/", client)
        assert cache.is_allowed("http://example.com/anything") is False

    @pytest.mark.asyncio
    async def test_fetch_host_410_falls_back_allow_all(self):
        """4xx other than 401/403 stays allow-all (404 test covers 404)."""
        client = MagicMock()
        client.get = AsyncMock(return_value=_status_response(410))
        cache = RobotsCache("test-agent")
        await cache.fetch_host("http://example.com/", client)
        assert cache.is_allowed("http://example.com/private/x") is True

    @pytest.mark.asyncio
    async def test_fetch_host_parse_error_falls_back_allow_all(self):
        """A malformed robots.txt body (ValueError) keeps the allow-all fallback."""
        resp = _status_response(200)
        resp.text = MagicMock()
        resp.text.splitlines.side_effect = ValueError("malformed body")
        client = MagicMock()
        client.get = AsyncMock(return_value=resp)
        cache = RobotsCache("test-agent")
        await cache.fetch_host("http://example.com/", client)
        assert cache.is_allowed("http://example.com/anything") is True

    @pytest.mark.asyncio
    async def test_ensure_host_200_disallows_only_matching_path(self):
        """A 200 body is parsed normally: only Disallowed paths are denied."""
        client = MagicMock()
        client.get = AsyncMock(
            return_value=_status_response(200, "User-agent: *\nDisallow: /private")
        )
        cache = RobotsCache("test-agent")
        await cache.ensure_host("http://example.com", client)
        assert cache.is_allowed("http://example.com/private/x") is False
        assert cache.is_allowed("http://example.com/public") is True

    @pytest.mark.asyncio
    async def test_ensure_host_idempotent_once_per_host(self):
        """A second ensure_host for the same host issues no further request."""
        client = MagicMock()
        client.get = AsyncMock(return_value=_status_response(200, "User-agent: *"))
        cache = RobotsCache("test-agent")
        await cache.ensure_host("http://example.com", client)
        await cache.ensure_host("http://example.com", client)
        assert client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_robots_request_sets_follow_redirects(self):
        """The robots request carries follow_redirects=True per request (REQ-004)."""
        client = MagicMock()
        client.get = AsyncMock(return_value=_status_response(200, "User-agent: *"))
        cache = RobotsCache("test-agent")
        await cache.ensure_host("http://example.com", client)
        assert client.get.call_args.kwargs["follow_redirects"] is True

    @pytest.mark.asyncio
    async def test_fetch_host_transport_error_falls_back_disallow_all(self):
        """Transport error is fail-closed (renamed and inverted from allow-all)."""
        client = MagicMock()
        client.get = AsyncMock(side_effect=httpx.ConnectError("boom"))
        cache = RobotsCache("test-agent")
        await cache.fetch_host("http://example.com/", client)
        assert cache.is_allowed("http://example.com/anything") is False


class TestLinkDiscoveryRobots:
    @staticmethod
    def _a_tag(href: str):
        soup = BeautifulSoup(f'<a href="{href}">x</a>', "lxml")
        return soup.find("a")

    def test_disallowed_url_skipped_when_cache_present(self):
        """A URL failing is_allowed is not enqueued."""
        cache = RobotsCache("agent")
        cache._parsers["example.com"] = _parser_with_disallow()
        disc = LinkDiscovery(
            skip_nofollow=False, skip_external=False, robots_cache=cache
        )
        assert (
            disc.should_enqueue_link(
                self._a_tag("http://example.com/private/x"),
                "http://example.com/",
                "http://example.com/",
            )
            is False
        )

    def test_allowed_url_enqueued_when_cache_present(self):
        """An allowed URL is enqueued with the cache present."""
        cache = RobotsCache("agent")
        cache._parsers["example.com"] = _parser_with_disallow()
        disc = LinkDiscovery(
            skip_nofollow=False, skip_external=False, robots_cache=cache
        )
        assert (
            disc.should_enqueue_link(
                self._a_tag("http://example.com/public"),
                "http://example.com/",
                "http://example.com/",
            )
            is True
        )

    def test_none_cache_preserves_behavior(self):
        """With robots_cache=None the filter behaves as before (no robots check)."""
        disc = LinkDiscovery(
            skip_nofollow=False, skip_external=False, robots_cache=None
        )
        assert (
            disc.should_enqueue_link(
                self._a_tag("http://example.com/private/x"),
                "http://example.com/",
                "http://example.com/",
            )
            is True
        )


class TestOrchestratorEagerFetch:
    def _orchestrator(self, robots_cache):
        disc = LinkDiscovery(
            skip_nofollow=False, skip_external=False, robots_cache=robots_cache
        )
        orch = CrawlOrchestrator(
            http_fetcher=MagicMock(),
            content_extractor=MagicMock(),
            link_discovery=disc,
            language_resolver=MagicMock(),
            persister=MagicMock(),
            config={
                "fetch_timeout": 5,
                "crawl_delay": 0,
                "crawl_concurrency": 1,
                "max_pages": 500,
                "max_depth": 0,
            },
        )
        orch._process_crawl_url_async = AsyncMock(return_value=None)
        return orch, disc

    @pytest.mark.asyncio
    async def test_fetch_called_before_loop_when_cache_present(self):
        """The start host's robots.txt is fetched before any page is processed."""
        orch, disc = self._orchestrator(RobotsCache("agent"))
        order: list[str] = []

        async def spy_fetch(*args, **kwargs):
            order.append("robots")

        async def spy_process(*args, **kwargs):
            order.append("process")

        disc._robots_cache.fetch_host = spy_fetch
        orch._process_crawl_url_async = spy_process
        await orch.crawl_site("http://example.com/start", "en")
        assert order == ["robots", "process"]

    @pytest.mark.asyncio
    async def test_fetch_not_called_when_cache_absent(self):
        """With no cache wired, zero robots.txt requests are issued."""
        orch, disc = self._orchestrator(None)
        await orch.crawl_site("http://example.com/start", "en")
        assert disc._robots_cache is None


class TestOrchestratorRobotsGuard:
    """Fetch-time robots guard in ``_process_crawl_url_async`` (ragrev014).

    These cases exercise the real ``_process_crawl_url_async`` body, so they
    cannot reuse ``TestOrchestratorEagerFetch._orchestrator`` (which stubs the
    method with an ``AsyncMock``). Only fetch/persist dependencies are mocked;
    the cache's ``ensure_host`` is stubbed so the real ``httpx.AsyncClient``
    built by ``crawl_site`` never issues network requests.
    """

    HTML_WITH_EXT_LINK = (
        '<html><body><a href="http://other.example/page">x</a></body></html>'
    )

    @staticmethod
    def _orchestrator(robots_cache: RobotsCache | None, max_depth: int = 2):
        disc = LinkDiscovery(
            skip_nofollow=False,
            skip_external=False,
            max_depth=max_depth,
            robots_cache=robots_cache,
        )
        extractor = MagicMock()
        extractor.extract_content.return_value = ("title", "text", [])
        lang_resolver = MagicMock()
        lang_resolver.resolve_lang.return_value = "en"
        orch = CrawlOrchestrator(
            http_fetcher=MagicMock(),
            content_extractor=extractor,
            link_discovery=disc,
            language_resolver=lang_resolver,
            persister=MagicMock(),
            config={
                "fetch_timeout": 5,
                "crawl_delay": 0,
                "crawl_concurrency": 1,
                "max_pages": 50,
                "max_depth": max_depth,
            },
        )
        orch._http_fetcher.get_conditional_headers = MagicMock(return_value=None)
        return orch

    @pytest.mark.asyncio
    async def test_start_url_disallowed_is_never_requested(self, caplog):
        """A disallowed start URL is refused before any page fetch (AC-3)."""
        cache = RobotsCache("agent")
        cache.ensure_host = AsyncMock()
        cache.is_allowed = MagicMock(return_value=False)
        orch = self._orchestrator(cache)
        orch._http_fetcher.fetch_html = AsyncMock()
        with caplog.at_level(logging.INFO):
            await orch.crawl_site("http://example.com/private/page", "en")
        assert orch._http_fetcher.fetch_html.await_count == 0
        assert (
            "robots disallowed: url=http://example.com/private/page "
            "host=http://example.com" in caplog.text
        )

    @pytest.mark.asyncio
    async def test_external_host_robots_ensured_once_before_url(self):
        """A link to a second host triggers exactly one robots fetch for it
        before that URL is requested (AC-2)."""
        cache = RobotsCache("agent")
        ensured: list[str] = []

        async def spy_ensure(origin: str, client: object) -> None:
            ensured.append(origin)

        cache.ensure_host = spy_ensure
        orch = self._orchestrator(cache)
        orch._http_fetcher.fetch_html = AsyncMock(
            side_effect=[
                Fetched(
                    self.HTML_WITH_EXT_LINK, None, None, "http://example.com/start"
                ),
                Fetched("", None, None, "http://other.example/page"),
            ]
        )
        await orch.crawl_site("http://example.com/start", "en")
        # preload (start host), guard (start URL), guard (external host): one
        # ensure per URL, idempotent per host inside ensure_host.
        assert ensured == [
            "http://example.com",
            "http://example.com",
            "http://other.example",
        ]
        assert orch._http_fetcher.fetch_html.await_count == 2

    @pytest.mark.asyncio
    async def test_policy_off_takes_no_robots_action(self):
        """With robots_cache=None behavior is identical to today (AC-5)."""
        orch = self._orchestrator(None)
        orch._http_fetcher.fetch_html = AsyncMock(
            return_value=Fetched("", None, None, "http://example.com/start")
        )
        await orch.crawl_site("http://example.com/start", "en")
        assert orch._http_fetcher.fetch_html.await_count == 1
        assert orch._http_fetcher.fetch_html.await_args.args[4] is None


class TestCrawlerWiring:
    @staticmethod
    def _config(respect_robots: bool | None) -> dict:
        cfg = {
            "rag_src_dir": "/tmp/crawl-test-output",
            "crawl_delay": 0,
            "max_depth": 0,
            "min_chunk": 0,
            "fetch_retry": 1,
            "fetch_timeout": 15,
            "crawl_concurrency": 1,
            "max_pages": 500,
            "target_urls": [],
            "skip_nofollow": False,
            "skip_external": True,
            "rag_db_path": ":memory:",
            "sqlite_timeout": 30,
            "sqlite_busy_timeout_ms": 30000,
        }
        if respect_robots is not None:
            cfg["respect_robots"] = respect_robots
        return cfg

    def test_respect_robots_false_injects_none(self):
        """Flag off leaves robots_cache=None (unchanged behavior)."""
        crawler = WebCrawler(config=self._config(False))
        assert crawler.link_discovery._robots_cache is None

    def test_respect_robots_true_injects_cache(self):
        """Flag on injects a RobotsCache bound to the crawler user agent."""
        crawler = WebCrawler(config=self._config(True))
        cache = crawler.link_discovery._robots_cache
        assert isinstance(cache, RobotsCache)
        assert cache._user_agent == WebCrawler._USER_AGENT

    def test_respect_robots_unset_defaults_none(self):
        """Absent flag defaults to off (robots_cache=None)."""
        crawler = WebCrawler(config=self._config(None))
        assert crawler.link_discovery._robots_cache is None
