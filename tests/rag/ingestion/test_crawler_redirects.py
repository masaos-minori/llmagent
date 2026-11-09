"""Redirect trust-boundary tests for the WebCrawler (ragrev012).

Two layers:

* ``TestRedirectAllowedPolicy`` / ``TestHostIsPublicPolicy`` unit-test the pure
  policy helpers in :mod:`rag.ingestion.crawler_utils`. They select under
  ``-k policy`` and never touch the network.
* ``TestCrawlRedirects`` drives ``WebCrawler.crawl_site`` through a respx mock
  transport so every redirect stays inside the process. The refused cases assert
  that nothing is persisted; because the pre-implementation client follows
  redirects automatically, those assertions fail on HEAD and pass once the hop
  policy lands (AC-6).
"""

import asyncio
import asyncio.base_events
import ipaddress
import logging
import socket
from pathlib import Path

import pytest
import respx
from httpx import Response
from rag.ingestion.crawler import WebCrawler
from rag.ingestion.crawler_utils import host_is_public, redirect_allowed

START = "http://example.com/start"
UPGRADE_TARGET = "https://example.com/landing"
DOWNGRADE_TARGET = "http://example.com/landing"


def _page(text: str, links: tuple[str, ...] = ()) -> str:
    """Return a minimal HTML page whose body text is long enough to persist."""
    anchors = "".join(f'<a href="{href}">{href.strip("/")}</a>' for href in links)
    return (
        f"<html><body><h1>{text}</h1>"
        f"<p>{text} body content long enough to be persisted by the crawler.</p>"
        f"{anchors}</body></html>"
    )


def _saved_urls(rag_src_dir: str) -> list[str]:
    """Return the url field of every crawl JSON written under rag_src_dir."""
    import json

    return [
        json.loads(path.read_bytes())["url"]
        for path in Path(rag_src_dir).glob("*.json")
    ]


@pytest.fixture
def crawl_config():
    """Return a minimal config dict for WebCrawler initialization."""
    return {
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
        "rag_db_path": "",
        "sqlite_timeout": 30,
        "sqlite_busy_timeout_ms": 30000,
    }


@pytest.fixture
def stub_dns(monkeypatch):
    """Resolve hosts through a controllable map; literal IPs pass through.

    ``host_is_public`` resolves via the loop's asynchronous ``getaddrinfo``;
    patching it keeps named targets (e.g. ``localhost``) off the real network
    and makes the public/private matrix deterministic.
    """

    dns: dict[str, list[str]] = {}

    async def fake_getaddrinfo(self, host: str, *args, **kwargs):
        if host in dns:
            addresses = dns[host]
        else:
            try:
                ipaddress.ip_address(host)
            except ValueError:
                # Unknown non-literal host resolves to nothing -> fail closed.
                return []
            addresses = [host]
        return [
            (socket.AF_INET, socket.SOCK_STREAM, 6, "", (ip, 0)) for ip in addresses
        ]

    # host_is_public resolves via the running loop's getaddrinfo; patch the
    # method where it is actually defined (BaseEventLoop) so every loop subclass
    # picks up the stub without touching the real network.
    monkeypatch.setattr(
        asyncio.base_events.BaseEventLoop, "getaddrinfo", fake_getaddrinfo
    )
    return dns


# ── Policy unit tests (select under -k policy) ────────────────────────────────


class TestRedirectAllowedPolicy:
    """Unit tests for redirect_allowed (REQ-002)."""

    def test_same_host_same_scheme_allowed(self):
        """A same-host, same-scheme hop is allowed."""
        assert redirect_allowed("http://example.com/a", "http://example.com/b") is True

    def test_http_to_https_upgrade_allowed(self):
        """An http->https upgrade on the same host is allowed."""
        assert redirect_allowed(START, UPGRADE_TARGET) is True

    def test_downgrade_refused(self):
        """An https->http downgrade on the same host is refused."""
        assert redirect_allowed("https://example.com/a", DOWNGRADE_TARGET) is False

    def test_default_port_normalized(self):
        """Default ports are normalized away, so the upgrade still matches."""
        assert (
            redirect_allowed("http://example.com", "https://example.com:443/x") is True
        )

    def test_cross_host_refused_by_origin(self):
        """A different host is refused here and falls through to the address check."""
        assert redirect_allowed(START, "http://10.0.0.5/secret") is False


class TestHostIsPublicPolicy:
    """Unit tests for host_is_public (REQ-002)."""

    @pytest.mark.asyncio
    async def test_public_literal_ip(self):
        """A global IPv4 address is public."""
        assert await host_is_public("93.184.216.34") is True

    @pytest.mark.asyncio
    async def test_loopback_refused(self):
        """Loopback is not public."""
        assert await host_is_public("127.0.0.1") is False

    @pytest.mark.asyncio
    async def test_link_local_refused(self):
        """Link-local (cloud metadata) is not public."""
        assert await host_is_public("169.254.169.254") is False

    @pytest.mark.asyncio
    async def test_private_range_refused(self):
        """Private ranges are not public."""
        assert await host_is_public("192.168.1.10") is False
        assert await host_is_public("10.10.10.10") is False

    @pytest.mark.asyncio
    async def test_named_host_public_when_stubbed_public(self, stub_dns):
        """A name resolving only to public addresses is public."""
        stub_dns["example.org"] = ["93.184.216.34"]
        assert await host_is_public("example.org") is True

    @pytest.mark.asyncio
    async def test_named_host_refused_when_stubbed_loopback(self, stub_dns):
        """A name resolving to loopback is refused."""
        stub_dns["internal.test"] = ["127.0.0.1"]
        assert await host_is_public("internal.test") is False

    @pytest.mark.asyncio
    async def test_unknown_host_fails_closed(self, stub_dns):
        """A name with no resolution fails closed (not public)."""
        assert await host_is_public("nope.test") is False


# ── Integration tests (mock transport through crawl_site) ─────────────────────


class TestCrawlRedirects:
    """End-to-end redirect handling through WebCrawler.crawl_site (REQ-001/002/004)."""

    @staticmethod
    def _config(crawl_config, tmp_path):
        config = dict(crawl_config)
        config["rag_src_dir"] = str(tmp_path)
        return config

    @staticmethod
    def _redirect(target: str):
        """Return a respx handler that answers any request with a 307 to target."""

        def handler(request):
            return Response(307, headers={"Location": target})

        return handler

    @pytest.mark.parametrize(
        "start,target",
        [
            pytest.param(START, "http://127.0.0.1:8042/secret", id="loopback"),
            pytest.param(START, "http://169.254.169.254/latest", id="metadata"),
            pytest.param(START, "http://10.0.0.5/secret", id="private-range"),
            pytest.param(START, "http://localhost:8042/secret", id="named-loopback"),
            pytest.param(
                "https://example.com/start",
                DOWNGRADE_TARGET,
                id="downgrade",
            ),
        ],
    )
    async def test_refused_hop_persists_nothing(
        self,
        crawl_config,
        tmp_path,
        stub_dns,
        start,
        target,
    ):
        """AC-2: a cross-origin or internal hop is refused and nothing is persisted.

        On HEAD the client follows the redirect and persists the reached body, so
        this assertion fails before the hop policy lands.
        """
        if "localhost" in target:
            stub_dns["localhost"] = ["127.0.0.1"]
        config = self._config(crawl_config, tmp_path)

        with respx.mock:
            respx.get(start).mock(side_effect=self._redirect(target))
            respx.get(target).mock(return_value=Response(200, text=_page("Reached")))
            await WebCrawler(config=config).crawl_site(start, "en")

        assert _saved_urls(config["rag_src_dir"]) == []

    async def test_same_host_upgrade_followed_and_persisted_under_final_url(
        self,
        crawl_config,
        tmp_path,
    ):
        """AC-4: an http->https upgrade on the same host is followed and persisted under the final URL."""
        config = self._config(crawl_config, tmp_path)

        with respx.mock:
            respx.get(START).mock(side_effect=self._redirect(UPGRADE_TARGET))
            respx.get(UPGRADE_TARGET).mock(
                return_value=Response(200, text=_page("Landing"))
            )
            await WebCrawler(config=config).crawl_site(START, "en")

        assert _saved_urls(config["rag_src_dir"]) == [UPGRADE_TARGET]

    async def test_redirect_loop_refused_with_distinct_log(
        self,
        crawl_config,
        tmp_path,
        caplog,
    ):
        """AC-1: a redirect loop ends as failed with a distinct log and persists nothing."""
        config = self._config(crawl_config, tmp_path)
        a = "http://example.com/a"
        b = "http://example.com/b"

        with respx.mock:
            respx.get(a).mock(side_effect=self._redirect(b))
            respx.get(b).mock(side_effect=self._redirect(a))
            with caplog.at_level(logging.WARNING, logger="rag.ingestion.http_fetcher"):
                await WebCrawler(config=config).crawl_site(a, "en")

        assert _saved_urls(config["rag_src_dir"]) == []
        assert any("redirect" in r.getMessage().lower() for r in caplog.records)

    async def test_over_long_chain_refused(
        self,
        crawl_config,
        tmp_path,
    ):
        """AC-1: a redirect chain longer than the hop limit is refused and persists nothing.

        On HEAD the client follows the whole chain and persists the final page, so
        this assertion fails before the hop policy lands.
        """
        config = self._config(crawl_config, tmp_path)
        hops = 12
        chain = [f"http://example.com/p{i}" for i in range(hops)]

        with respx.mock:
            for i, url in enumerate(chain):
                next_url = chain[i + 1] if i + 1 < hops else url
                respx.get(url).mock(side_effect=self._redirect(next_url))
            await WebCrawler(config=config).crawl_site(chain[0], "en")

        assert _saved_urls(config["rag_src_dir"]) == []

    async def test_robots_denied_hop_persists_nothing(
        self,
        crawl_config,
        tmp_path,
    ):
        """AC-3: a robots-disallowed hop is refused and nothing is persisted.

        With ``respect_robots`` on, the start host's robots.txt disallows the
        redirected path; the hop policy refuses the hop before requesting it.
        """
        config = self._config(crawl_config, tmp_path)
        config["respect_robots"] = True
        start = "http://example.com/start"
        denied = "http://example.com/private/x"

        with respx.mock:
            respx.get("http://example.com/robots.txt").mock(
                return_value=Response(200, text="User-agent: *\nDisallow: /private/")
            )
            respx.get(start).mock(side_effect=self._redirect(denied))
            respx.get(denied).mock(return_value=Response(200, text=_page("Reached")))
            await WebCrawler(config=config).crawl_site(start, "en")

        assert _saved_urls(config["rag_src_dir"]) == []
