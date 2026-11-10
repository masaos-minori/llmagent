"""Integration tests for WebCrawler with respx-based HTTP mocking."""

import asyncio
import logging
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import respx
from httpx import Response
from rag.ingestion.crawler import WebCrawler


@pytest.fixture
def mock_config():
    """Return a minimal config dict for WebCrawler initialization."""
    return {
        "rag_src_dir": "/tmp/crawl-test-output",
        "crawl_delay": 0,
        "max_depth": 1,
        "min_chunk": 0,
        "fetch_retry": 1,
        "fetch_timeout": 15,
        "crawl_concurrency": 3,
        "max_pages": 500,
        "target_urls": [],
        "skip_nofollow": False,
        "skip_external": True,
        "rag_db_path": "",
        "sqlite_timeout": 30,
        "sqlite_busy_timeout_ms": 30000,
    }


class TestHttpRetryOnTransientFailure:
    """Verify HTTP retry on transient failures."""

    @pytest.mark.asyncio
    async def test_fetch_retry_on_http_error(self, mock_config):
        """HTTP errors trigger retries up to fetch_retry count."""
        import httpx
        from rag.ingestion.http_fetcher import FetchFailed, HttpFetcher

        client = MagicMock()
        resp_mock = MagicMock()
        resp_mock.raise_for_status.side_effect = httpx.HTTPStatusError(
            "network timeout", request=MagicMock(), response=resp_mock
        )
        client.get = AsyncMock(return_value=resp_mock)

        config = dict(mock_config)
        config["fetch_retry"] = 3
        fetcher = HttpFetcher(config=config)

        result = await fetcher.fetch_html(
            "http://example.com/page", client, extra_headers=None
        )

        assert result == FetchFailed()  # Exhausted retries
        assert client.get.call_count == 3

    @pytest.mark.asyncio
    async def test_success_after_retry(self, mock_config):
        """Successful response after initial failure returns content."""
        import httpx
        from rag.ingestion.http_fetcher import Fetched, HttpFetcher

        client = MagicMock()
        resp_mock = MagicMock()
        resp_mock.status_code = 200
        resp_mock.is_success = True
        resp_mock.text = "<html><body>Hello</body></html>"
        resp_mock.headers = {}

        # First call fails, second succeeds
        first_call = True

        async def side_effect(*args, **kwargs):
            nonlocal first_call
            if first_call:
                first_call = False
                raise httpx.HTTPStatusError(
                    "timeout", request=MagicMock(), response=MagicMock()
                )
            return resp_mock

        client.get = AsyncMock(side_effect=side_effect)

        config = dict(mock_config)
        config["fetch_retry"] = 2
        fetcher = HttpFetcher(config=config)

        result = await fetcher.fetch_html(
            "http://example.com/page", client, extra_headers=None
        )

        assert isinstance(result, Fetched)
        assert "Hello" in result.html
        assert client.get.call_count == 2


class TestResponseSkippingContentFetch:
    """Verify 304 response skipping content fetch."""

    @pytest.mark.asyncio
    async def test_304_skips_content_fetch(self, mock_config):
        """304 Not Modified returns NotModified, no content extraction."""
        from rag.ingestion.http_fetcher import HttpFetcher, NotModified

        client = MagicMock()
        resp_mock = MagicMock()
        resp_mock.status_code = 304
        resp_mock.is_success = True
        client.get = AsyncMock(return_value=resp_mock)

        fetcher = HttpFetcher(config=mock_config)

        result = await fetcher.fetch_html(
            "http://example.com/page", client, extra_headers=None
        )

        assert result == NotModified()
        assert client.get.call_count == 1

    @pytest.mark.asyncio
    async def test_conditional_headers_sent_with_request(self, mock_config):
        """Conditional headers are sent when available from DB lookup."""
        from rag.ingestion.http_fetcher import Fetched, HttpFetcher

        client = MagicMock()
        resp_mock = MagicMock()
        resp_mock.status_code = 200
        resp_mock.is_success = True
        resp_mock.text = "<html><body>Updated content</body></html>"
        resp_mock.headers = {"ETag": "abc123"}
        client.get = AsyncMock(return_value=resp_mock)

        config = dict(mock_config)
        config["rag_db_path"] = ":memory:"
        fetcher = HttpFetcher(config=config)

        # Mock DB to return conditional headers
        with patch.object(
            fetcher,
            "get_conditional_headers",
            return_value={
                "If-None-Match": "old-etag",
                "If-Modified-Since": "Mon, 01 Jan 2024 00:00:00 GMT",
            },
        ):
            result = await fetcher.fetch_html(
                "http://example.com/page",
                client,
                extra_headers={"If-None-Match": "old-etag"},
            )

        assert isinstance(result, Fetched)
        assert result.etag == "abc123"


class TestMaxPagesBoundaryCondition:
    """Verify the persisted-vs-scheduled page budget (raging009)."""

    @staticmethod
    def _page(text: str, links: tuple[str, ...] = ()) -> str:
        """Return a minimal HTML page whose body text is long enough to persist."""
        anchors = "".join(f'<a href="{href}">{href.strip("/")}</a>' for href in links)
        return (
            f"<html><body><h1>{text}</h1>"
            f"<p>{text} body content long enough to be persisted by the crawler.</p>"
            f"{anchors}</body></html>"
        )

    @staticmethod
    async def _drain_crawl_tasks(before: set[asyncio.Task]) -> None:
        """Cancel and await crawl tasks still live after crawl_site returns.

        On HEAD a budget stop leaves a fetch task in flight; cancelling and gathering
        it here (while the respx mock is still active) removes the orphan deterministically
        so the test neither leaks a live task into the next test nor warns on an
        unretrieved exception.
        """
        orphans = {
            t
            for t in asyncio.all_tasks()
            if t is not asyncio.current_task() and t not in before
        }
        for t in orphans:
            t.cancel()
        if orphans:
            await asyncio.gather(*orphans, return_exceptions=True)

    @pytest.mark.asyncio
    async def test_stops_at_max_pages(
        self,
        mock_config: dict,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """AC-1: the crawl stops when max_pages pages are persisted, not when URLs are scheduled."""
        mock_config["max_pages"] = 2
        mock_config["max_depth"] = 3
        mock_config["rag_src_dir"] = str(tmp_path)

        with respx.mock:
            respx.get("http://example.com/start").mock(
                return_value=Response(200, text=self._page("Alpha", ("/b",)))
            )
            respx.get("http://example.com/b").mock(
                return_value=Response(200, text=self._page("Bravo", ("/c", "/d")))
            )
            crawler = WebCrawler(config=mock_config)
            with caplog.at_level(logging.WARNING, logger="rag.ingestion.orchestrator"):
                await crawler.crawl_site("http://example.com/start", "en")

            assert len(list(tmp_path.glob("*-*.json"))) == 2
            assert len(respx.calls) == 2

        assert "persisted budget reached" in caplog.text

    @pytest.mark.asyncio
    async def test_none_save_result_not_counted(
        self,
        mock_config: dict,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """AC-5: a save_http result of None is not counted against the persisted budget and enqueues no links."""
        mock_config["max_pages"] = 1
        mock_config["max_depth"] = 3
        mock_config["rag_src_dir"] = str(tmp_path)

        with respx.mock:
            respx.get("http://example.com/start").mock(
                return_value=Response(200, text=self._page("Alpha", ("/b",)))
            )
            respx.get("http://example.com/b").mock(
                return_value=Response(200, text=self._page("Bravo", ("/c", "/d")))
            )
            crawler = WebCrawler(config=mock_config)
            with caplog.at_level(logging.WARNING, logger="rag.ingestion.orchestrator"):
                with patch.object(
                    crawler.crawl_persister, "save_http", return_value=None
                ):
                    await crawler.crawl_site("http://example.com/start", "en")

            assert len(list(tmp_path.glob("*-*.json"))) == 0
            assert "persisted budget reached" not in caplog.text
            assert len(respx.calls) == 1

    @pytest.mark.asyncio
    async def test_max_pages_warning_logged(
        self,
        mock_config: dict,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """AC-2: non-persisted fetches are capped at 2 * max_pages and the stop is logged."""
        mock_config["max_pages"] = 2
        mock_config["max_depth"] = 1
        mock_config["rag_src_dir"] = str(tmp_path)

        with respx.mock:
            respx.get("http://example.com/start").mock(
                return_value=Response(
                    200,
                    text=self._page("Alpha", tuple(f"/n{i}" for i in range(1, 7))),
                )
            )
            for i in range(1, 7):
                respx.get(f"http://example.com/n{i}").mock(
                    return_value=Response(status_code=304)
                )
            crawler = WebCrawler(config=mock_config)
            with caplog.at_level(logging.WARNING, logger="rag.ingestion.orchestrator"):
                await crawler.crawl_site("http://example.com/start", "en")

            assert len(respx.calls) <= 2 * mock_config["max_pages"]

        assert "scheduling budget reached" in caplog.text

    @pytest.mark.asyncio
    async def test_no_orphaned_tasks_after_budget_stop(
        self,
        mock_config: dict,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """AC-1/AC-4: a budget stop with a slow request in flight leaves no live task, no never-retrieved warning, and writes no file after return."""
        import httpx

        mock_config["max_pages"] = 2
        mock_config["max_depth"] = 2
        mock_config["rag_src_dir"] = str(tmp_path)
        release = asyncio.Event()

        async def slow_handler(request: httpx.Request) -> Response:
            await release.wait()
            return Response(200, text=self._page("Slow"))

        with respx.mock:
            respx.get("http://example.com/start").mock(
                return_value=Response(200, text=self._page("Alpha", ("/fast", "/slow")))
            )
            respx.get("http://example.com/fast").mock(
                return_value=Response(200, text=self._page("Fast"))
            )
            respx.get("http://example.com/slow").mock(side_effect=slow_handler)
            crawler = WebCrawler(config=mock_config)
            before = asyncio.all_tasks()
            files_after_return: list[Path] = []
            try:
                with caplog.at_level(
                    logging.WARNING,
                    logger="rag.ingestion.orchestrator",
                ):
                    await crawler.crawl_site("http://example.com/start", "en")
                files_after_return = sorted(tmp_path.glob("*-*.json"))
                assert asyncio.all_tasks() <= before
                assert len(files_after_return) == 2
            finally:
                release.set()
                await self._drain_crawl_tasks(before)

        assert sorted(tmp_path.glob("*-*.json")) == files_after_return
        assert "never retrieved" not in caplog.text

    @pytest.mark.asyncio
    async def test_cleanup_exception_logged_once(
        self,
        mock_config: dict,
        tmp_path: Path,
        caplog: pytest.LogCaptureFixture,
    ) -> None:
        """AC-2: a non-cancellation exception during cleanup is logged once and does not make crawl_site raise; cancelled tasks are silent."""
        import httpx

        mock_config["max_pages"] = 2
        mock_config["max_depth"] = 2
        mock_config["rag_src_dir"] = str(tmp_path)
        release = asyncio.Event()

        async def boom_handler(request: httpx.Request) -> Response:
            try:
                await release.wait()
            except asyncio.CancelledError:
                raise RuntimeError("cleanup boom") from None
            return Response(200, text=self._page("Boom"))

        with respx.mock:
            respx.get("http://example.com/start").mock(
                return_value=Response(200, text=self._page("Alpha", ("/fast", "/boom")))
            )
            respx.get("http://example.com/fast").mock(
                return_value=Response(200, text=self._page("Fast"))
            )
            respx.get("http://example.com/boom").mock(side_effect=boom_handler)
            crawler = WebCrawler(config=mock_config)
            before = asyncio.all_tasks()
            try:
                with caplog.at_level(
                    logging.ERROR,
                    logger="rag.ingestion.orchestrator",
                ):
                    await crawler.crawl_site("http://example.com/start", "en")
            finally:
                await self._drain_crawl_tasks(before)

        boom_logs = [r for r in caplog.records if "cleanup boom" in r.getMessage()]
        assert len(boom_logs) == 1
        assert "never retrieved" not in caplog.text

    def test_max_pages_fallback_default(self, mock_config):
        """Both consumers default max_pages to 200 (matching deployed config) when absent."""
        config_without_max_pages = {
            k: v for k, v in mock_config.items() if k != "max_pages"
        }

        crawler = WebCrawler(config=config_without_max_pages)

        assert crawler._max_pages == 200
        assert crawler.orchestrator._max_pages == 200


class TestBfsQueueOrdering:
    """Verify BFS queue ordering."""

    def test_bfs_processes_shallower_depths_first(self):
        """Shallower URLs are processed before deeper ones (FIFO order)."""
        import asyncio

        queue = asyncio.Queue()
        queue.put_nowait(("http://a.com/page1", 0))
        queue.put_nowait(("http://b.com/page2", 0))
        queue.put_nowait(("http://c.com/page3", 1))
        queue.put_nowait(("http://d.com/page4", 1))

        # Dequeue should yield depth-first order
        urls = []
        while not queue.empty():
            url, depth = queue.get_nowait()
            urls.append((url, depth))

        # First two should be depth 0
        assert urls[0][1] == 0
        assert urls[1][1] == 0
        # Next two should be depth 1
        assert urls[2][1] == 1
        assert urls[3][1] == 1

    def test_visited_prevents_duplicate_processing(self):
        """Visited URLs are not re-enqueued during BFS."""
        visited = set()
        queue = asyncio.Queue()

        # Enqueue same URL twice
        queue.put_nowait(("http://example.com/page", 0))
        queue.put_nowait(("http://example.com/page", 0))

        # Process first occurrence
        url, depth = queue.get_nowait()
        visited.add(url)

        # Second occurrence should be skipped
        url2, depth2 = queue.get_nowait()
        if url2 in visited:
            # Would skip — this is the expected behavior
            assert True
        else:
            assert False


class TestLinkFiltering:
    """Verify link filtering behavior."""

    def test_nofollow_links_excluded_when_skip_nofollow_true(self, mock_config):
        """Links with rel=nofollow are excluded when skip_nofollow=True."""
        from bs4 import BeautifulSoup
        from rag.ingestion.link_discovery import LinkDiscovery

        mock_config["skip_nofollow"] = True
        discovery = LinkDiscovery(skip_nofollow=True, skip_external=False)

        html = '<a href="http://example.com/link" rel="nofollow">nofollow</a>'
        soup = BeautifulSoup(html, "lxml")
        a_tag = soup.find("a")

        result = discovery.should_enqueue_link(
            a_tag, "http://start.com/", "http://start.com/"
        )
        assert result is False

    def test_nofollow_links_included_when_skip_nofollow_false(self, mock_config):
        """Links with rel=nofollow are included when skip_nofollow=False."""
        from bs4 import BeautifulSoup
        from rag.ingestion.link_discovery import LinkDiscovery

        mock_config["skip_nofollow"] = False
        mock_config["skip_external"] = False  # Allow external links too
        discovery = LinkDiscovery(skip_nofollow=False, skip_external=False)

        html = '<a href="http://example.com/link" rel="nofollow">nofollow</a>'
        soup = BeautifulSoup(html, "lxml")
        a_tag = soup.find("a")

        result = discovery.should_enqueue_link(
            a_tag, "http://start.com/", "http://start.com/"
        )
        assert result is True

    def test_cross_origin_links_excluded_when_skip_external_true(self, mock_config):
        """Cross-origin links are excluded when skip_external=True."""
        from bs4 import BeautifulSoup
        from rag.ingestion.link_discovery import LinkDiscovery

        mock_config["skip_external"] = True
        discovery = LinkDiscovery(skip_nofollow=False, skip_external=True)

        html = '<a href="http://other-domain.com/link">external</a>'
        soup = BeautifulSoup(html, "lxml")
        a_tag = soup.find("a")

        result = discovery.should_enqueue_link(
            a_tag, "http://same-origin.com/page", "http://same-origin.com/"
        )
        assert result is False

    def test_same_origin_links_included_when_skip_external_true(self, mock_config):
        """Same-origin links are included even when skip_external=True."""
        from bs4 import BeautifulSoup
        from rag.ingestion.link_discovery import LinkDiscovery

        mock_config["skip_external"] = True
        discovery = LinkDiscovery(skip_nofollow=False, skip_external=True)

        html = '<a href="/page">internal</a>'
        soup = BeautifulSoup(html, "lxml")
        a_tag = soup.find("a")

        result = discovery.should_enqueue_link(
            a_tag, "http://same-origin.com/page", "http://same-origin.com/"
        )
        assert result is True


class TestConditionalHeadersMisconfiguration:
    """Verify empty rag_db_path handling (crawl003, REQ-001/002/003)."""

    def test_get_conditional_headers_empty_path_returns_empty(self, mock_config):
        """Empty rag_db_path returns {} without raising ValueError (REQ-002)."""
        from rag.ingestion.http_fetcher import HttpFetcher

        fetcher = HttpFetcher(config=mock_config)
        result = fetcher.get_conditional_headers("http://example.com/page")

        assert result == {}

    def test_get_conditional_headers_valid_path_no_raise(self, mock_config):
        """A configured path does not raise; missing table yields {} (REQ-003)."""
        from rag.ingestion.http_fetcher import HttpFetcher

        config = dict(mock_config)
        config["rag_db_path"] = ":memory:"
        fetcher = HttpFetcher(config=config)

        # No documents table in a fresh :memory: DB -> caught OperationalError.
        result = fetcher.get_conditional_headers("http://example.com/page")

        assert result == {}

    def test_get_conditional_headers_empty_path_warning_deduped(
        self, mock_config, caplog
    ):
        """The empty-path warning is logged once across repeated calls (REQ-002 dedupe)."""
        import logging

        from rag.ingestion.http_fetcher import HttpFetcher

        fetcher = HttpFetcher(config=mock_config)
        with caplog.at_level(logging.WARNING, logger="rag.ingestion.http_fetcher"):
            fetcher.get_conditional_headers("http://example.com/a")
            fetcher.get_conditional_headers("http://example.com/b")

        warnings = [
            r
            for r in caplog.records
            if "rag_db_path is not configured" in r.getMessage()
        ]
        assert len(warnings) == 1

    @pytest.mark.asyncio
    async def test_crawl_raises_on_empty_rag_db_for_http(
        self,
        mock_config,
    ):
        """crawl() raises when an HTTP target exists but rag_db_path is empty (REQ-001)."""
        mock_config["target_urls"] = [("http://example.com/start", "en")]

        crawler = WebCrawler(config=mock_config)

        with pytest.raises(RuntimeError, match="rag_db_path"):
            await crawler.crawl()

    @pytest.mark.asyncio
    async def test_crawl_empty_path_ok_for_file_targets_only(
        self,
        mock_config,
        tmp_path,
    ):
        """crawl() with only file:// targets passes the rag_db_path preflight (REQ-004)."""
        mock_config["target_urls"] = []
        crawler = WebCrawler(config=mock_config)
        target = tmp_path / "doc.txt"
        target.write_text("short")

        # No RuntimeError: file:// targets never reach the conditional-header cache.
        await crawler.crawl([(f"file://{target.resolve()}", "auto")])


class TestSessionDbParameter:
    """Verify get_conditional_headers db parameter (crawl004, REQ-001/003/004)."""

    @staticmethod
    def _seeded_helper(tmp_path):
        """Open a helper on a rag db file seeded with one documents row."""
        from db.helper import SQLiteHelper

        helper = SQLiteHelper(
            db_path=str(tmp_path / "rag.db"),
            sqlite_timeout=30,
            sqlite_busy_timeout_ms=30000,
        )
        helper.open(write_mode=True, row_factory=True)
        helper.execute(
            "CREATE TABLE documents "
            "(url TEXT PRIMARY KEY, etag TEXT, last_modified TEXT)"
        )
        helper.execute(
            "INSERT INTO documents (url, etag, last_modified) VALUES (?, ?, ?)",
            ("http://example.com/page", "etag-1", "Mon, 01 Jan 2024 00:00:00 GMT"),
        )
        helper.commit()
        return helper

    def test_db_parameter_returns_same_headers_as_per_call(self, mock_config, tmp_path):
        """Session-helper headers are identical to the per-call lookup (REQ-003)."""
        from rag.ingestion.http_fetcher import HttpFetcher

        config = dict(mock_config)
        config["rag_db_path"] = str(tmp_path / "rag.db")
        fetcher = HttpFetcher(config=config)
        helper = self._seeded_helper(tmp_path)

        with_db = fetcher.get_conditional_headers("http://example.com/page", db=helper)
        without_db = fetcher.get_conditional_headers("http://example.com/page")

        assert with_db == {
            "If-None-Match": "etag-1",
            "If-Modified-Since": "Mon, 01 Jan 2024 00:00:00 GMT",
        }
        assert with_db == without_db
        helper.close()

    def test_db_parameter_not_closed_by_lookup(self, mock_config, tmp_path):
        """Passing a session helper must leave the connection open for reuse (REQ-001)."""
        from rag.ingestion.http_fetcher import HttpFetcher

        config = dict(mock_config)
        config["rag_db_path"] = str(tmp_path / "rag.db")
        fetcher = HttpFetcher(config=config)
        helper = self._seeded_helper(tmp_path)

        fetcher.get_conditional_headers("http://example.com/page", db=helper)

        assert helper.conn is not None
        helper.close()

    def test_db_parameter_query_error_absorbed(self, mock_config, tmp_path):
        """Query errors on the session helper are absorbed into {} (REQ-004 parity)."""
        from db.helper import SQLiteHelper
        from rag.ingestion.http_fetcher import HttpFetcher

        helper = SQLiteHelper(
            db_path=":memory:",
            sqlite_timeout=30,
            sqlite_busy_timeout_ms=30000,
        )
        helper.open(row_factory=True)  # No documents table in a fresh DB
        config = dict(mock_config)
        config["rag_db_path"] = str(tmp_path / "rag.db")
        fetcher = HttpFetcher(config=config)

        assert (
            fetcher.get_conditional_headers("http://example.com/page", db=helper) == {}
        )
        helper.close()


class TestSessionConnectionLifecycle:
    """Verify one SQLiteHelper per crawl_site session (crawl004, REQ-001/002/003)."""

    @staticmethod
    def _spy_connections(monkeypatch):
        """Record every SQLiteHelper open/close instance for the test body."""
        import db.helper as db_helper

        opens: list = []
        closes: list = []
        orig_open = db_helper.SQLiteHelper.open
        orig_close = db_helper.SQLiteHelper.close

        def spy_open(self, *args, **kwargs):
            result = orig_open(self, *args, **kwargs)
            opens.append(self)
            return result

        def spy_close(self):
            closes.append(self)
            orig_close(self)

        monkeypatch.setattr(db_helper.SQLiteHelper, "open", spy_open)
        monkeypatch.setattr(db_helper.SQLiteHelper, "close", spy_close)
        return opens, closes

    @staticmethod
    def _seed_documents(db_path):
        """Create the documents table with one row before the crawl opens its session."""
        from db.helper import SQLiteHelper

        helper = SQLiteHelper(
            db_path=db_path,
            sqlite_timeout=30,
            sqlite_busy_timeout_ms=30000,
        )
        helper.open(write_mode=True)
        helper.execute(
            "CREATE TABLE documents "
            "(url TEXT PRIMARY KEY, etag TEXT, last_modified TEXT)"
        )
        helper.execute(
            "INSERT INTO documents (url, etag, last_modified) VALUES (?, ?, ?)",
            ("http://example.com/page", "etag-1", "Mon, 01 Jan 2024 00:00:00 GMT"),
        )
        helper.commit()
        helper.close()

    def _rag_config(self, mock_config, tmp_path):
        config = dict(mock_config)
        config["rag_db_path"] = str(tmp_path / "rag.db")
        config["rag_src_dir"] = str(tmp_path / "rag-src")
        return config

    @pytest.mark.asyncio
    async def test_one_open_one_close_per_session(
        self, mock_config, tmp_path, monkeypatch
    ):
        """A crawl_site session opens and closes exactly one shared connection (REQ-001)."""
        opens, closes = self._spy_connections(monkeypatch)
        crawler = WebCrawler(config=self._rag_config(mock_config, tmp_path))
        crawler.orchestrator._drain_queue_to_tasks = MagicMock(return_value=set())

        await crawler.crawl_site("http://example.com/", "en")

        assert len(opens) == 1
        assert len(closes) == 1
        assert opens[0] is closes[0]

    @pytest.mark.asyncio
    async def test_session_db_closed_on_exception(
        self, mock_config, tmp_path, monkeypatch
    ):
        """The session connection is closed when the BFS loop raises (REQ-002)."""
        opens, closes = self._spy_connections(monkeypatch)
        crawler = WebCrawler(config=self._rag_config(mock_config, tmp_path))
        crawler.orchestrator._drain_queue_to_tasks = MagicMock(
            side_effect=RuntimeError("boom")
        )

        with pytest.raises(RuntimeError, match="boom"):
            await crawler.crawl_site("http://example.com/", "en")

        assert len(closes) == 1

    @pytest.mark.asyncio
    async def test_headers_lookup_uses_session_connection(
        self, mock_config, tmp_path, monkeypatch
    ):
        """Conditional headers come from the session connection, with no per-call open (REQ-003)."""
        from rag.ingestion.http_fetcher import FetchFailed

        self._seed_documents(str(tmp_path / "rag.db"))
        opens, closes = self._spy_connections(monkeypatch)
        crawler = WebCrawler(config=self._rag_config(mock_config, tmp_path))
        fetcher = crawler.orchestrator._http_fetcher
        # FetchFailed, not NotModified: a 304 below the depth limit would trigger the
        # discovery fetch and break the single-await assertion below.
        fetcher.fetch_html = AsyncMock(return_value=FetchFailed())

        await crawler.crawl_site("http://example.com/page", "en")

        fetcher.fetch_html.assert_awaited_once()
        call = fetcher.fetch_html.await_args
        extra_headers = (
            call.args[2] if len(call.args) > 2 else call.kwargs.get("extra_headers")
        )
        assert extra_headers == {
            "If-None-Match": "etag-1",
            "If-Modified-Since": "Mon, 01 Jan 2024 00:00:00 GMT",
        }
        assert len(opens) == 1
        assert len(closes) == 1


class TestNotModifiedLinkDiscovery:
    """Verify a not-modified page still reaches its subtree (ragrev011, REQ-002/003/004/005)."""

    START = "http://example.com/page"
    CHILD = "http://example.com/child"
    FOREIGN = "http://other.example.com/out"

    @staticmethod
    def _page(text: str, links: tuple[str, ...] = ()) -> str:
        """Return a minimal HTML page whose body text is long enough to persist."""
        anchors = "".join(f'<a href="{href}">{href.strip("/")}</a>' for href in links)
        return (
            f"<html><body><h1>{text}</h1>"
            f"<p>{text} body content long enough to be persisted by the crawler.</p>"
            f"{anchors}</body></html>"
        )

    @staticmethod
    def _config(mock_config: dict, tmp_path: Path, max_depth: int) -> dict:
        """Point rag_db_path and rag_src_dir at tmp_path with an explicit depth limit."""
        config = dict(mock_config)
        config["rag_db_path"] = str(tmp_path / "rag.db")
        config["rag_src_dir"] = str(tmp_path / "rag-src")
        config["max_depth"] = max_depth
        config["skip_external"] = True
        return config

    @staticmethod
    def _saved_urls(rag_src_dir: str) -> list[str]:
        """Return the url field of every crawl JSON written under rag_src_dir."""
        import json

        return [
            json.loads(path.read_bytes())["url"]
            for path in Path(rag_src_dir).glob("*.json")
        ]

    def _start_route(self, links: tuple[str, ...]):
        """Return a respx side effect: 304 for a conditional request, a linked page otherwise."""
        import httpx

        def handler(request: httpx.Request) -> Response:
            if request.headers.get("if-none-match"):
                return Response(status_code=304)
            return Response(200, text=self._page("Index", links))

        return handler

    @pytest.mark.asyncio
    async def test_304_start_page_discovers_changed_child(
        self, mock_config: dict, tmp_path: Path
    ) -> None:
        """A 304 start page is re-fetched without validators and its changed child is persisted (REQ-002, REQ-003, REQ-005)."""
        TestSessionConnectionLifecycle._seed_documents(str(tmp_path / "rag.db"))
        config = self._config(mock_config, tmp_path, max_depth=1)

        with respx.mock:
            respx.get(self.START).mock(
                side_effect=self._start_route(("/child", self.FOREIGN))
            )
            respx.get(self.CHILD).mock(
                return_value=Response(200, text=self._page("Child"))
            )
            respx.get(self.FOREIGN).mock(
                return_value=Response(200, text=self._page("Foreign"))
            )
            crawler = WebCrawler(config=config)
            await crawler.crawl_site(self.START, "en")

            requested = [str(call.request.url) for call in respx.calls]
            assert requested == [self.START, self.START, self.CHILD]
            assert respx.calls[0].request.headers.get("if-none-match") == "etag-1"
            assert "if-none-match" not in respx.calls[1].request.headers
            assert not respx.get(self.FOREIGN).called

        assert self._saved_urls(config["rag_src_dir"]) == [self.CHILD]

    @pytest.mark.asyncio
    async def test_304_at_depth_limit_makes_no_extra_request(
        self, mock_config: dict, tmp_path: Path
    ) -> None:
        """A not-modified page at the depth limit makes no discovery fetch (REQ-002)."""
        TestSessionConnectionLifecycle._seed_documents(str(tmp_path / "rag.db"))
        config = self._config(mock_config, tmp_path, max_depth=0)

        with respx.mock:
            respx.get(self.START).mock(side_effect=self._start_route(("/child",)))
            respx.get(self.CHILD).mock(
                return_value=Response(200, text=self._page("Child"))
            )
            crawler = WebCrawler(config=config)
            await crawler.crawl_site(self.START, "en")

            assert len(respx.calls) == 1
            assert not respx.get(self.CHILD).called

        assert self._saved_urls(config["rag_src_dir"]) == []

    @pytest.mark.asyncio
    async def test_failed_fetch_and_304_log_distinctly(
        self, mock_config: dict, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """A failed fetch logs a warning and a 304 logs info, and neither enqueues links without a body (REQ-004)."""
        import httpx

        config = self._config(mock_config, tmp_path, max_depth=1)
        config["fetch_retry"] = 1

        def fail(request: httpx.Request) -> Response:
            raise httpx.ConnectError("boom")

        with respx.mock:
            respx.get(self.START).mock(side_effect=fail)
            respx.get(self.CHILD).mock(
                return_value=Response(200, text=self._page("Child"))
            )
            with caplog.at_level(logging.INFO, logger="rag.ingestion.orchestrator"):
                await WebCrawler(config=config).crawl_site(self.START, "en")
            failed_log = [r.getMessage() for r in caplog.records]
            assert not respx.get(self.CHILD).called

        caplog.clear()
        with respx.mock:
            respx.get(self.START).mock(return_value=Response(status_code=304))
            respx.get(self.CHILD).mock(
                return_value=Response(200, text=self._page("Child"))
            )
            with caplog.at_level(logging.INFO, logger="rag.ingestion.orchestrator"):
                await WebCrawler(config=config).crawl_site(self.START, "en")
            not_modified_log = [r.getMessage() for r in caplog.records]
            assert not respx.get(self.CHILD).called

        assert any("fetch failed, subtree not discovered" in m for m in failed_log)
        assert not any("not modified" in m for m in failed_log)
        assert any("not modified" in m for m in not_modified_log)
        assert not any(
            "fetch failed, subtree not discovered" in m for m in not_modified_log
        )
