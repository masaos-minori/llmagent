#!/usr/bin/env python3
"""scripts/rag/ingestion/http_fetcher.py

HttpFetcher: owns HTTP fetching concern (retry, conditional headers).

Extracted from WebCrawler to separate HTTP fetching from BFS orchestration.
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
from http import HTTPStatus
from typing import TYPE_CHECKING

import httpx

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class HttpFetcher:
    """Owns HTTP fetching: retrying fetch and conditional-header lookup."""

    _USER_AGENT = "Mozilla/5.0 (compatible; RAG-bot/1.0; +local)"

    def __init__(self, config: dict) -> None:
        self._fetch_retry: int = int(config.get("fetch_retry", 3))
        self._fetch_timeout: float = float(config.get("fetch_timeout", 15))
        self._sqlite_timeout: int = int(config.get("sqlite_timeout", 30))
        self._sqlite_busy_timeout_ms: int = int(
            config.get("sqlite_busy_timeout_ms", 30000)
        )
        self._rag_db_path: str = str(config.get("rag_db_path", ""))

    async def fetch_html(
        self,
        url: str,
        client: httpx.AsyncClient,
        extra_headers: dict[str, str] | None = None,
    ) -> tuple[str, str | None, str | None] | None:
        """Fetch HTML with optional conditional request headers; returns (html, etag, last_modified) on 200, None on 304 or retry exhaustion."""
        req_headers = dict(extra_headers or {})
        for i in range(self._fetch_retry):
            try:
                resp = await client.get(url, headers=req_headers)
                if resp.status_code == HTTPStatus.NOT_MODIFIED:
                    logger.info(
                        "%s Not Modified, skipping: %s",
                        HTTPStatus.NOT_MODIFIED,
                        url,
                    )
                    return None
                resp.raise_for_status()
                etag = resp.headers.get("ETag") or resp.headers.get("etag")
                last_modified = resp.headers.get("Last-Modified") or resp.headers.get(
                    "last-modified",
                )
                return resp.text, etag, last_modified
            except httpx.HTTPError as e:
                logger.warning(
                    "fetch failed (%s/%s) %s: %s", i + 1, self._fetch_retry, url, e
                )
                if i < self._fetch_retry - 1:
                    await asyncio.sleep(min(2**i, 10))
        return None

    def get_conditional_headers(self, url: str) -> dict[str, str]:
        """Return If-None-Match/If-Modified-Since headers from the cached document."""
        from db.helper import SQLiteHelper

        try:
            with SQLiteHelper(
                db_path=self._rag_db_path,
                sqlite_timeout=self._sqlite_timeout,
                sqlite_busy_timeout_ms=self._sqlite_busy_timeout_ms,
            ).open(row_factory=True) as db:
                rows = db.fetchall(
                    "SELECT etag, last_modified FROM documents WHERE url = ?",
                    (url,),
                )
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
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
