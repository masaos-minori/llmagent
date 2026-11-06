#!/usr/bin/env python3
"""scripts/rag/ingestion/orchestrator.py

CrawlOrchestrator: owns BFS queue/semaphore loop concern.

Extracted from WebCrawler to separate BFS orchestration from component concerns.
"""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING
from urllib.parse import urlparse

import httpx

if TYPE_CHECKING:
    from db.helper import SQLiteHelper

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

# Scheduling bound as a multiple of the persisted-page budget (raging009): non-persisted
# fetches (304, empty content, rejected language, failures) consume scheduling only.
SCHEDULED_BUDGET_MULTIPLIER = 2


@dataclass
class _CrawlBudget:
    """Per-crawl_site page-budget state: persisted count and scheduling bound."""

    persisted: int = 0
    max_persist: int = 0
    max_scheduled: int = 0


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
        # Session-scoped SQLite connection settings (crawl004); parsed like HttpFetcher.
        self._rag_db_path: str = str(config.get("rag_db_path", ""))
        self._sqlite_timeout: int = int(config.get("sqlite_timeout", 30))
        self._sqlite_busy_timeout_ms: int = int(
            config.get("sqlite_busy_timeout_ms", 30000)
        )

    async def crawl_site(self, start_url: str, hint_lang: str) -> None:
        """Async BFS crawl within the same origin up to max_depth levels via asyncio.Semaphore concurrency and FIRST_COMPLETED loop; max_pages bounds persisted pages and 2 * max_pages bounds scheduled URLs."""
        sem = asyncio.Semaphore(self._concurrency)
        queue: asyncio.Queue[tuple[str, int]] = asyncio.Queue()
        visited: set[str] = set()
        pending: set[asyncio.Task] = set()
        budget = _CrawlBudget(
            max_persist=self._max_pages,
            max_scheduled=self._max_pages * SCHEDULED_BUDGET_MULTIPLIER,
        )
        queue.put_nowait((normalize_url(start_url), 0))

        async with httpx.AsyncClient(
            headers=self._HEADERS,
            timeout=self._fetch_timeout,
            follow_redirects=True,
        ) as client:
            # One SQLite connection per crawl_site session (crawl004): opened here,
            # reused by every conditional-header lookup, closed on any exit path.
            session_db: SQLiteHelper | None = None
            if self._rag_db_path:
                from db.helper import SQLiteHelper

                session_db = SQLiteHelper(
                    db_path=self._rag_db_path,
                    sqlite_timeout=self._sqlite_timeout,
                    sqlite_busy_timeout_ms=self._sqlite_busy_timeout_ms,
                ).open(reuse_connection=True, row_factory=True)
            # crawl005: eagerly load robots.txt for the start host so the policy
            # is enforced before the first page request. No-op when disabled.
            robots_cache = getattr(self._link_discovery, "_robots_cache", None)
            if robots_cache is not None:
                parsed_start = urlparse(normalize_url(start_url))
                origin = f"{parsed_start.scheme}://{parsed_start.netloc}"
                await robots_cache.fetch_host(origin, client)
            try:
                while not queue.empty() or pending:
                    if budget.persisted >= budget.max_persist:
                        logger.warning(
                            "persisted budget reached: persisted=%d max_pages=%d for %s",
                            budget.persisted,
                            budget.max_persist,
                            start_url,
                        )
                        break
                    if len(visited) >= budget.max_scheduled:
                        logger.warning(
                            "scheduling budget reached: scheduled=%d max_pages=%d for %s",
                            len(visited),
                            budget.max_persist,
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
                        session_db,
                        budget,
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
                logger.info(
                    "BFS stop: scheduled=%d persisted=%d max_pages=%d",
                    len(visited),
                    budget.persisted,
                    budget.max_persist,
                )
            finally:
                if session_db is not None:
                    session_db.close()

    def _drain_queue_to_tasks(
        self,
        queue: asyncio.Queue,
        visited: set[str],
        start_url: str,
        hint_lang: str,
        client: httpx.AsyncClient,
        sem: asyncio.Semaphore,
        session_db: SQLiteHelper | None,
        budget: _CrawlBudget,
    ) -> set[asyncio.Task]:
        """Dequeue all pending URLs and create fetch tasks for unvisited ones, stopping as soon as the scheduling bound is reached."""
        tasks: set[asyncio.Task] = set()
        while not queue.empty():
            url, depth = queue.get_nowait()
            if url in visited or depth > self._max_depth:
                continue
            if len(visited) >= budget.max_scheduled:
                break
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
                        session_db,
                        budget,
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
        session_db: SQLiteHelper | None,
        budget: _CrawlBudget,
    ) -> None:
        """Fetch, extract, save one URL and enqueue its outbound links; counts the saved page against the persisted budget."""
        async with sem:
            logger.info("[depth=%s] %s", depth, url)
            await asyncio.sleep(self._crawl_delay)

            extra_headers = self._http_fetcher.get_conditional_headers(
                url, db=session_db
            )
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
            budget.persisted += 1
            self._link_discovery.enqueue_links(html, url, start_url, depth, queue)
