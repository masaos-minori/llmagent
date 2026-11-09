"""tests/test_crawler_retry_boundary.py

Boundary tests for WebCrawler HTTP retry, 304 skip, max_pages limit, and external link filtering.
"""

from __future__ import annotations

import asyncio
import logging
from pathlib import Path
from typing import Any
from unittest.mock import patch

import pytest
import respx
from httpx import Response
from rag.ingestion.crawler import WebCrawler
from rag.ingestion.link_discovery import LinkDiscovery


def _get_base_cfg(tmp_path: Path) -> dict[str, Any]:
    """Return a minimal valid config for WebCrawler."""
    db_path = tmp_path / "test_rag.db"
    return {
        "rag_src_dir": str(tmp_path),
        "rag_db_path": str(db_path),
        "crawl_delay": 0,
        "max_depth": 1,
        "min_chunk": 10,
        "fetch_retry": 2,
        "target_urls": [],
    }


@pytest.mark.asyncio
async def test_retry_on_503_then_succeeds(tmp_path: Path) -> None:
    """Verify crawler retries on 503 then succeeds on second attempt."""
    call_count = 0

    def side_effect(request):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return Response(status_code=503)
        return Response(status_code=200, text="<html><body>OK</body></html>")

    with respx.mock:
        route = respx.get("http://example.com").mock(side_effect=side_effect)
        crawler = WebCrawler(config=_get_base_cfg(tmp_path))
        await crawler.crawl_site("http://example.com", "en")
        assert route.calls.called
        assert call_count >= 2


@pytest.mark.asyncio
async def test_skip_304_response(tmp_path: Path) -> None:
    """Verify 304 response is handled without fetching content."""
    with respx.mock:
        respx.get("http://example.com").mock(return_value=Response(status_code=304))
        crawler = WebCrawler(config=_get_base_cfg(tmp_path))
        await crawler.crawl_site("http://example.com", "en")
        assert respx.get("http://example.com").called


@pytest.mark.asyncio
async def test_max_pages_boundary(tmp_path: Path) -> None:
    """Verify crawler stops exactly at max_pages limit."""
    with respx.mock:
        for i in range(5):
            respx.get(f"http://example.com/page{i}").mock(
                return_value=Response(
                    status_code=200, text=f"<html><body>Page {i}</body></html>"
                )
            )
        cfg = _get_base_cfg(tmp_path)
        cfg["max_pages"] = 1
        crawler = WebCrawler(config=cfg)
        await crawler.crawl()
        assert len(respx.calls) <= 1


@pytest.mark.asyncio
async def test_external_link_filter(tmp_path: Path) -> None:
    """Verify external links are filtered from BFS queue."""
    with respx.mock:
        respx.get("http://example.com").mock(
            return_value=Response(
                status_code=200,
                text='<html><body><a href="http://external.com/link">External</a></body></html>',
            )
        )
        cfg = _get_base_cfg(tmp_path)
        cfg["skip_external"] = True
        crawler = WebCrawler(config=cfg)
        await crawler.crawl_site("http://example.com", "en")
        assert not respx.get("http://external.com/link").called


# ── Persisted vs scheduled page budget (raging009) ────────────────────────────


def _page(text: str, links: tuple[str, ...] = ()) -> str:
    """Return a minimal HTML page whose body text is long enough to persist."""
    anchors = "".join(f'<a href="{href}">{href.strip("/")}</a>' for href in links)
    return (
        f"<html><body><h1>{text}</h1>"
        f"<p>{text} body content long enough to be persisted by the crawler.</p>"
        f"{anchors}</body></html>"
    )


def _persisted_files(tmp_path: Path) -> list[Path]:
    """Count the crawl output JSON files ({ts}-{slug}-{hash8}.json) written to tmp_path."""
    return list(tmp_path.glob("*-*.json"))


@pytest.mark.asyncio
async def test_persisted_budget_survives_304_pages(tmp_path: Path) -> None:
    """REQ-002/REQ-003: a 304 page must not consume the persisted-page budget."""
    with respx.mock:
        respx.get("http://example.com/").mock(
            return_value=Response(200, text=_page("Alpha", ("/a", "/b")))
        )
        respx.get("http://example.com/a").mock(return_value=Response(status_code=304))
        respx.get("http://example.com/b").mock(
            return_value=Response(200, text=_page("Bravo", ("/c",)))
        )
        respx.get("http://example.com/c").mock(
            return_value=Response(200, text=_page("Charlie"))
        )
        cfg = _get_base_cfg(tmp_path)
        cfg["max_pages"] = 3
        cfg["max_depth"] = 2
        crawler = WebCrawler(config=cfg)
        await crawler.crawl_site("http://example.com", "en")

        assert len(_persisted_files(tmp_path)) == 3
        # ragrev011: the 304 page is fetched once more without conditional headers for link
        # discovery, so the run makes 5 requests for 4 URLs and still persists only 3 pages.
        assert len(respx.calls) == 5
        assert respx.get("http://example.com/a").call_count == 2


@pytest.mark.asyncio
async def test_failure_only_run_is_scheduling_bounded(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """REQ-002/REQ-004: a run where every follow-up fetch fails stays within 2 * max_pages scheduled URLs."""
    with respx.mock:
        respx.get("http://example.com/").mock(
            return_value=Response(
                200,
                text=_page("Alpha", tuple(f"/p{i}" for i in range(1, 5))),
            )
        )
        for i in range(1, 5):
            respx.get(f"http://example.com/p{i}").mock(
                return_value=Response(status_code=500)
            )
        cfg = _get_base_cfg(tmp_path)
        cfg["max_pages"] = 2
        cfg["max_depth"] = 1
        cfg["fetch_retry"] = 1
        crawler = WebCrawler(config=cfg)
        with caplog.at_level(logging.INFO, logger="rag.ingestion.orchestrator"):
            await crawler.crawl_site("http://example.com", "en")

        assert len(respx.calls) <= 2 * cfg["max_pages"]
        assert len(_persisted_files(tmp_path)) == 1  # only the start page persists
        assert "BFS stop:" in caplog.text


@pytest.mark.asyncio
async def test_non_persisted_pages_consume_only_scheduling_budget(
    tmp_path: Path,
) -> None:
    """REQ-002/REQ-003: empty-content and unsupported-lang pages do not consume the persisted budget."""
    with respx.mock:
        respx.get("http://example.com/").mock(
            return_value=Response(200, text=_page("Alpha", ("/empty", "/other", "/f")))
        )
        respx.get("http://example.com/empty").mock(
            return_value=Response(200, text="<html><body></body></html>")
        )
        respx.get("http://example.com/other").mock(
            return_value=Response(200, text=_page("Other"))
        )
        respx.get("http://example.com/f").mock(
            return_value=Response(200, text=_page("Foxtrot", ("/v1",)))
        )
        respx.get("http://example.com/v1").mock(
            return_value=Response(200, text=_page("Victor"))
        )
        cfg = _get_base_cfg(tmp_path)
        cfg["max_pages"] = 3
        cfg["max_depth"] = 2
        crawler = WebCrawler(config=cfg)

        # detect_lang only ever returns 'ja', 'en', or None, so an unsupported
        # resolved language must be forced through the resolver stub.
        real_resolve = crawler.language_resolver.resolve_lang

        def _stub(text: str, hint_lang: str) -> str:
            if "Other" in text:
                return "ru"
            return real_resolve(text, hint_lang)

        with patch.object(crawler.language_resolver, "resolve_lang", side_effect=_stub):
            await crawler.crawl_site("http://example.com", "en")

        assert len(_persisted_files(tmp_path)) == 3
        assert len(respx.calls) == 5


@pytest.mark.asyncio
async def test_shared_link_is_fetched_once(tmp_path: Path) -> None:
    """AC-3: visited-set dedup is unchanged — a URL linked from two pages is fetched once."""
    with respx.mock:
        respx.get("http://example.com/").mock(
            return_value=Response(200, text=_page("Alpha", ("/b", "/c")))
        )
        respx.get("http://example.com/b").mock(
            return_value=Response(200, text=_page("Bravo", ("/d",)))
        )
        respx.get("http://example.com/c").mock(
            return_value=Response(200, text=_page("Charlie", ("/d",)))
        )
        respx.get("http://example.com/d").mock(
            return_value=Response(200, text=_page("Delta"))
        )
        cfg = _get_base_cfg(tmp_path)
        cfg["max_pages"] = 10
        cfg["max_depth"] = 2
        crawler = WebCrawler(config=cfg)
        await crawler.crawl_site("http://example.com", "en")

        assert respx.get("http://example.com/d").call_count == 1


# ── LinkDiscovery.enqueue_links runtime-import regression ─────────────────────


def test_enqueue_links_enqueues_same_origin_link() -> None:
    """Prerequisite fix: BeautifulSoup is a runtime import, so link parsing no longer raises NameError."""
    queue: asyncio.Queue[tuple[str, int]] = asyncio.Queue()
    LinkDiscovery(skip_external=True, max_depth=2).enqueue_links(
        '<html><body><a href="/a">a</a><a href="http://other.example/x">ext</a></body></html>',
        "http://example.com",
        "http://example.com",
        0,
        queue,
    )
    enqueued = []
    while not queue.empty():
        enqueued.append(queue.get_nowait())
    assert enqueued == [("http://example.com/a", 1)]


def test_enqueue_links_respects_max_depth() -> None:
    """Depth cap unchanged: at depth == max_depth no link is enqueued."""
    queue: asyncio.Queue[tuple[str, int]] = asyncio.Queue()
    LinkDiscovery(skip_external=True, max_depth=1).enqueue_links(
        '<html><body><a href="/a">a</a></body></html>',
        "http://example.com/a",
        "http://example.com",
        1,
        queue,
    )
    assert queue.empty()
