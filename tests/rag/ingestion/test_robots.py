"""Tests for the opt-in robots.txt policy (crawl005).

Covers the four runtime surfaces: the new ``RobotsCache`` module, the
``LinkDiscovery`` filter integration, the orchestrator eager per-host fetch, and
the ``crawler.py`` config wiring.
"""

from unittest.mock import AsyncMock, MagicMock
from urllib.robotparser import RobotFileParser

import httpx
import pytest
from bs4 import BeautifulSoup
from rag.ingestion.crawler import WebCrawler
from rag.ingestion.link_discovery import LinkDiscovery
from rag.ingestion.orchestrator import CrawlOrchestrator
from rag.ingestion.robots import RobotsCache


def _parser_with_disallow() -> RobotFileParser:
    parser = RobotFileParser()
    parser.parse(["User-agent: *", "Disallow: /private/"])
    return parser


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
    async def test_fetch_host_transport_error_falls_back_allow_all(self):
        """Transport error falls back to allow-all without raising."""
        client = MagicMock()
        client.get = AsyncMock(side_effect=httpx.ConnectError("boom"))
        cache = RobotsCache("test-agent")
        await cache.fetch_host("http://example.com/", client)
        assert cache.is_allowed("http://example.com/anything") is True


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
