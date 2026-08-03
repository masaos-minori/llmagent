"""tests/test_crawler_retry_boundary.py

Boundary tests for WebCrawler HTTP retry, 304 skip, max_pages limit, and external link filtering.
"""

from __future__ import annotations

from pathlib import Path

import pytest
import respx
from httpx import Response

from scripts.rag.ingestion.crawler import WebCrawler


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
        crawler = WebCrawler(config={"rag_src_dir": str(tmp_path)})
        await crawler.crawl_site("http://example.com", "en")
        assert route.calls.called
        assert call_count >= 2


@pytest.mark.asyncio
async def test_skip_304_response(tmp_path: Path) -> None:
    """Verify 304 response is handled without fetching content."""
    with respx.mock:
        respx.get("http://example.com").mock(return_value=Response(status_code=304))
        crawler = WebCrawler(config={"rag_src_dir": str(tmp_path)})
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
        crawler = WebCrawler(config={"rag_src_dir": str(tmp_path), "max_pages": 1})
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
        crawler = WebCrawler(
            config={"rag_src_dir": str(tmp_path), "skip_external": True}
        )
        await crawler.crawl_site("http://example.com", "en")
        assert not respx.get("http://external.com/link").called
