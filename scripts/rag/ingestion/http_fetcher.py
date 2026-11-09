#!/usr/bin/env python3
"""scripts/rag/ingestion/http_fetcher.py

HttpFetcher: owns HTTP fetching concern (retry, conditional headers, redirect hops).

Extracted from WebCrawler to separate HTTP fetching from BFS orchestration.
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING
from urllib.parse import urldefrag, urljoin, urlparse

import httpx
from rag.ingestion.crawler_utils import (
    host_is_public,
    redirect_allowed,
)

if TYPE_CHECKING:
    from db.helper import SQLiteHelper
    from rag.ingestion.robots import RobotsCache

logger = logging.getLogger(__name__)

# Status codes that represent a redirect the hop loop must resolve itself.
_REDIRECT_STATUS: frozenset[int] = frozenset({301, 302, 303, 307, 308})
# Hard bound on redirect hops (REQ-001); a loop or an over-long chain past this
# returns the failed outcome with a distinct log.
_MAX_REDIRECT_HOPS = 8


@dataclass(frozen=True)
class Fetched:
    html: str
    etag: str | None
    last_modified: str | None
    final_url: str


@dataclass(frozen=True)
class NotModified:
    pass


@dataclass(frozen=True)
class FetchFailed:
    pass


FetchResult = Fetched | NotModified | FetchFailed


class HttpFetcher:
    """Owns HTTP fetching: retrying fetch, conditional-header lookup, and redirect hops."""

    _USER_AGENT = "Mozilla/5.0 (compatible; RAG-bot/1.0; +local)"

    def __init__(self, config: dict) -> None:
        self._fetch_retry: int = int(config.get("fetch_retry", 3))
        self._fetch_timeout: float = float(config.get("fetch_timeout", 15))
        self._sqlite_timeout: int = int(config.get("sqlite_timeout", 30))
        self._sqlite_busy_timeout_ms: int = int(
            config.get("sqlite_busy_timeout_ms", 30000)
        )
        self._rag_db_path: str = str(config.get("rag_db_path", ""))
        # Guards against logging the empty-path warning on every fetch when
        # rag_db_path is misconfigured (see get_conditional_headers).
        self._logged_empty_path: bool = False

    async def fetch_html(
        self,
        url: str,
        client: httpx.AsyncClient,
        extra_headers: dict[str, str] | None = None,
        origin: str | None = None,
        robots_cache: RobotsCache | None = None,
    ) -> FetchResult:
        """Fetch HTML and follow redirects hop by hop until a non-redirect response or a refusal.

        ``origin`` is the crawl start URL (``scheme://netloc``); each redirect hop
        is validated against it before it is requested (REQ-001/REQ-002). Returns
        ``Fetched`` (with the final accepted URL) on a 200, ``NotModified`` on a
        304, and ``FetchFailed`` on retry exhaustion, a missing Location header, a
        refused hop, or a chain longer than :data:`_MAX_REDIRECT_HOPS`.
        """
        req_headers = dict(extra_headers or {})
        current_url = url
        for _hop in range(_MAX_REDIRECT_HOPS):
            response = await self._request_with_retry(current_url, req_headers, client)
            if response is None:
                return FetchFailed()
            if response.status_code == HTTPStatus.NOT_MODIFIED:
                logger.info(
                    "%s Not Modified: %s",
                    HTTPStatus.NOT_MODIFIED,
                    current_url,
                )
                return NotModified()
            if response.status_code not in _REDIRECT_STATUS:
                return self._build_fetched(response, current_url)
            target = self._redirect_target(response, current_url)
            if target is None:
                return FetchFailed()
            allowed, reason = await self._hop_policy(origin, target, robots_cache)
            if not allowed:
                logger.error("refused redirect hop: %s (%s)", target, reason)
                return FetchFailed()
            current_url = target
        logger.error(
            "redirect chain exceeds %d hops, refusing: %s",
            _MAX_REDIRECT_HOPS,
            url,
        )
        return FetchFailed()

    async def _request_with_retry(
        self,
        url: str,
        req_headers: dict[str, str],
        client: httpx.AsyncClient,
    ) -> httpx.Response | None:
        """Request ``url`` with back-off retries; return the response or None after retry exhaustion."""
        for i in range(self._fetch_retry):
            try:
                response = await client.get(url, headers=req_headers)
                # Only 4xx/5xx responses are real fetch errors worth retrying.
                # ``is_error`` is False for 2xx, 304, and redirects, so those
                # pass through to their upstream handling instead of raising.
                if response.is_error:
                    response.raise_for_status()
                return response
            except httpx.HTTPError as e:
                logger.warning(
                    "fetch failed (%s/%s) %s: %s",
                    i + 1,
                    self._fetch_retry,
                    url,
                    e,
                )
                if i < self._fetch_retry - 1:
                    await asyncio.sleep(min(2**i, 10))
        logger.warning("fetch failed after %s retries: %s", self._fetch_retry, url)
        return None

    async def _hop_policy(
        self,
        origin: str | None,
        url: str,
        robots_cache: RobotsCache | None = None,
    ) -> tuple[bool, str]:
        """Return ``(allowed, reason)`` for following a redirect hop to ``url``.

        A hop to the crawl start host is governed by :func:`redirect_allowed`
        (same scheme or an http-to-https upgrade allowed, a downgrade refused); a
        hop to any other host is allowed only when every resolved address is public
        (:func:`host_is_public`, fail closed). A configured robots cache then
        disallows a hop path for a host whose parser is loaded (REQ-003).
        """
        origin_host = urlparse(origin).hostname if origin else None
        url_host = urlparse(url).hostname
        if origin_host is not None and url_host == origin_host:
            if not redirect_allowed(origin, url):
                return False, "same-host downgrade refused"
        elif not await host_is_public(url_host):
            return False, "non-public destination"
        if robots_cache is not None and not robots_cache.is_allowed(url):
            return False, "robots denied"
        return True, ""

    @staticmethod
    def _redirect_target(response: httpx.Response, current_url: str) -> str | None:
        """Resolve the redirect Location against ``current_url``; None when absent."""
        location: str | None = response.headers.get("Location")
        if not location:
            return None
        target = urljoin(current_url, location)
        target, _ = urldefrag(target)
        return target.rstrip("/")

    @staticmethod
    def _build_fetched(response: httpx.Response, final_url: str) -> Fetched:
        """Build a ``Fetched`` outcome from a non-redirect response, carrying its final URL."""
        etag = response.headers.get("ETag") or response.headers.get("etag")
        last_modified = response.headers.get("Last-Modified") or response.headers.get(
            "last-modified"
        )
        return Fetched(response.text, etag, last_modified, final_url)

    def get_conditional_headers(
        self,
        url: str,
        db: SQLiteHelper | None = None,
    ) -> dict[str, str]:
        """Return If-None-Match/If-Modified-Since headers from the cached document.

        db: optional session-scoped SQLiteHelper (already opened with
        row_factory=True) to reuse instead of opening a per-call connection
        (crawl004). When None, the per-call open path runs unchanged.
        """
        from db.helper import SQLiteHelper

        if not self._rag_db_path:
            if not self._logged_empty_path:
                logger.warning(
                    "rag_db_path is not configured; skipping conditional-header "
                    "cache lookup for %s",
                    url,
                )
                self._logged_empty_path = True
            return {}
        query = "SELECT etag, last_modified FROM documents WHERE url = ?"
        try:
            if db is not None:
                rows = db.fetchall(query, (url,))
            else:
                with SQLiteHelper(
                    db_path=self._rag_db_path,
                    sqlite_timeout=self._sqlite_timeout,
                    sqlite_busy_timeout_ms=self._sqlite_busy_timeout_ms,
                ).open(row_factory=True) as local_db:
                    rows = local_db.fetchall(query, (url,))
        except (
            sqlite3.OperationalError,
            sqlite3.DatabaseError,
            ValueError,
        ) as e:
            logger.debug("DB lookup for conditional headers failed (%s): %s", url, e)
            return {}
        if not rows:
            return {}
        row = rows[0]
        hdrs: dict[str, str] = {}
        if row["etag"]:
            hdrs["If-None-Match"] = row["etag"]
        if row["last_modified"]:
            hdrs["If-Modified-Since"] = row["last_modified"]
        return hdrs
