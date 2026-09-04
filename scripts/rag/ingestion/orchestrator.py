#!/usr/bin/env python3
"""scripts/rag/ingestion/orchestrator.py

CrawlOrchestrator: owns BFS queue/semaphore loop concern.

Extracted from WebCrawler to separate BFS orchestration from component concerns.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Import here to avoid circular imports
from rag.ingestion.content_extractor import (
    ContentExtractor,  # noqa: E402 — local import for circular dependency avoidance
)
from rag.ingestion.crawl_persister import (
    CrawlPersister,  # noqa: E402 — local import for circular dependency avoidance
)
from rag.ingestion.crawler_utils import (
    normalize_url,  # noqa: E402 — local import for circular dependency avoidance
)
from rag.ingestion.http_fetcher import (
    HttpFetcher,  # noqa: E402 — local import for circular dependency avoidance
)
from rag.ingestion.language_resolver import (
    LanguageResolver,  # noqa: E402 — local import for circular dependency avoidance
)
from rag.ingestion.link_discovery import (
    LinkDiscovery,  # noqa: E402 — local import for circular dependency avoidance
)


class CrawlOrchestrator:
    """Owns BFS queue/semaphore loop coordination."""

    _USER_AGENT = "Mozilla/5.0 (compatible; RAG-bot/1.0; +local)"
    # Class-level headers shared across all AsyncClient instances
    _HEADERS: dict[str, str] = {
        "User-Agent": _USER_AGENT,
        "Accept-Language": "ja,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }

    def __init__(
        self,
        http_fetcher: HttpFetcher,
        content_extractor: ContentExtractor,
        link_discovery: LinkDiscovery,
        language_resolver: LanguageResolver,
        persister: CrawlPersister,
        config: dict,
    ) -> None:
        self._http_fetcher = http_fetcher
        self._content_extractor = content_extractor
        self._link_discovery = link_discovery
        self._language_resolver = language_resolver
        self._persister = persister
        self._fetch_timeout: float = float(config.get("fetch_timeout", 15))
        self._crawl_delay: float = float(config.get("crawl_delay", 0))
        self._max_depth: int = int(config.get("max_depth", 0))
        self._concurrency: int = int(config.get("crawl_concurrency", 3))
        self._max_pages: int = int(config.get("max_pages", 500))

    async def crawl(self, targets: list[tuple[str, str]]) -> None:
        """Crawl all given targets."""
        for url, lang in targets:
            logger.info("=== start: %s (lang=%s) ===", url, lang)
            try:
                if url.startswith("file://"):
                    # Local file handling delegated to persister
                    pass
                else:
                    await self.crawl_site(url, lang)
            except Exception as _crawl_err:
                logger.exception("crawl failed: %s: %s", url, _crawl_err)
            logger.info("=== done:  %s ===", url)

    async def crawl_site(self, start_url: str, hint_lang: str) -> None:
        """Async BFS crawl within the same origin up to max_depth levels via asyncio.Semaphore concurrency and FIRST_COMPLETED loop."""
        sem = asyncio.Semaphore(self._concurrency)
        queue: asyncio.Queue[tuple[str, int]] = asyncio.Queue()
        visited: set[str] = set()
        pending: set[asyncio.Task] = set()
        queue.put_nowait((normalize_url(start_url), 0))

        async with httpx.AsyncClient(
            headers=self._HEADERS,
            timeout=self._fetch_timeout,
            follow_redirects=True,
        ) as client:
            while not queue.empty() or pending:
                if len(visited) >= self._max_pages:
                    logger.warning(
                        "Reached max_pages=%s; stopping BFS at %s",
                        self._max_pages,
                        start_url,
                    )
                    break
                pending |= self._drain_queue_to_tasks(
                    queue,
                    visited,
                    start_url,
                    hint_lang,
                    client,
                    sem,
                )
                if not pending:
                    break
                done, pending = await asyncio.wait(
                    pending,
                    return_when=asyncio.FIRST_COMPLETED,
                )
                for t in done:
                    if exc := t.exception():
                        logger.error("Crawl task error: %s", exc)

    def _drain_queue_to_tasks(
        self,
        queue: asyncio.Queue,
        visited: set[str],
        start_url: str,
        hint_lang: str,
        client: httpx.AsyncClient,
        sem: asyncio.Semaphore,
    ) -> set[asyncio.Task]:
        """Dequeue all pending URLs and create fetch tasks for unvisited ones."""
        tasks: set[asyncio.Task] = set()
        while not queue.empty():
            url, depth = queue.get_nowait()
            if url in visited or depth > self._max_depth:
                continue
            visited.add(url)
            tasks.add(
                asyncio.create_task(
                    self._process_crawl_url_async(
                        url,
                        depth,
                        start_url,
                        hint_lang,
                        queue,
                        client,
                        sem,
                    ),
                ),
            )
        return tasks

    async def _process_crawl_url_async(
        self,
        url: str,
        depth: int,
        start_url: str,
        hint_lang: str,
        queue: asyncio.Queue,
        client: httpx.AsyncClient,
        sem: asyncio.Semaphore,
    ) -> None:
        """Fetch, extract, save one URL and enqueue its outbound links."""
        async with sem:
            logger.info("[depth=%s] %s", depth, url)
            await asyncio.sleep(self._crawl_delay)

            extra_headers = self._http_fetcher.get_conditional_headers(url)
            result = await self._http_fetcher.fetch_html(url, client, extra_headers)
            if result is None:
                return
            html, etag, last_modified = result

            title, text, code_blocks = self._content_extractor.extract_content(
                html, url
            )
            if not text and not code_blocks:
                logger.debug("no content: %s", url)
                return

            resolved_lang: str = self._language_resolver.resolve_lang(text, hint_lang)
            if resolved_lang not in frozenset({"en", "ja"}):
                logger.debug("lang=%r not supported: %s", resolved_lang, url)
                return

            fetched_at = datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ")
            self._persister.save_http(
                url,
                title,
                resolved_lang,
                text,
                code_blocks,
                etag,
                last_modified,
                fetched_at,
            )
            self._link_discovery.enqueue_links(html, url, start_url, depth, queue)
