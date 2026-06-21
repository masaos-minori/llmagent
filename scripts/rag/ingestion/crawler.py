#!/usr/bin/env python3
"""Crawler.py
BFS web crawler that saves extracted text and code blocks to rag-src/.
Entry point: python Crawler.py [--url URL ...] [--lang {en,ja}]

Output: rag-src/{timestamp}-{slug}.txt — JSON payload (not plain text).
Fields: url, title, lang, fetched_at, content, code_blocks, etag, last_modified.

Pipeline position: Crawler.py → ChunkSplitter.py → RagIngester.py
"""

import argparse
import asyncio
import sqlite3
from datetime import datetime
from http import HTTPStatus
from pathlib import Path
from typing import Any
from urllib.parse import urljoin, urlparse

import httpx
import orjson
from bs4 import BeautifulSoup
from db.helper import SQLiteHelper
from rag.ingestion.crawler_utils import (
    _SUPPORTED_LANGS,
    detect_lang,
    extract_text,
    normalize_url,
    parse_target_urls,
    same_origin,
    url_to_slug,
)
from rag.utils import MIN_TEXT_LENGTH_FOR_DETECTION, validate_url
from shared.config_loader import ConfigLoader
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/crawl.log")


# ──────────────────────────────────────────────────────────────────────────────
# Crawler class
# ──────────────────────────────────────────────────────────────────────────────
class WebCrawler:
    """BFS web crawler: extracts text and code blocks from same-origin pages and saves JSON files to rag-src/."""

    _USER_AGENT = "Mozilla/5.0 (compatible; RAG-bot/1.0; +local)"
    # Class-level headers shared across all AsyncClient instances
    _HEADERS: dict[str, str] = {
        "User-Agent": _USER_AGENT,
        "Accept-Language": "ja,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        cfg: dict[str, Any] = config or ConfigLoader().load("rag_pipeline.toml")
        self._rag_src_dir: Path = Path(cfg["rag_src_dir"])
        self._crawl_delay: float = float(cfg["crawl_delay"])
        self._max_depth: int = int(cfg["max_depth"])
        self._min_chunk: int = int(cfg["min_chunk"])
        self._fetch_retry: int = int(cfg["fetch_retry"])
        self._fetch_timeout: float = float(cfg.get("fetch_timeout", 15))
        self._concurrency: int = int(cfg.get("crawl_concurrency", 3))
        self._max_pages: int = int(cfg.get("max_pages", 500))
        self._target_urls: list[tuple[str, str]] = parse_target_urls(cfg["target_urls"])
        # Skip links with rel="nofollow" when True
        self._skip_nofollow: bool = bool(cfg.get("skip_nofollow", False))
        # Skip cross-origin links when True (default: True = same-origin only)
        self._skip_external: bool = bool(cfg.get("skip_external", True))

    # ── Public interface ──────────────────────────────────────────────────────

    def crawl_file(self, path: Path, lang: str) -> int:
        """Save a local file as a crawl result JSON in rag-src/; .py files stored as code blocks; returns 1 on success, 0 on failure."""
        # Guard: file must exist before reading
        if not path.exists():
            logger.error("Local file not found: %s", path)
            return 0
        try:
            content = path.read_text(encoding="utf-8", errors="ignore")
        except OSError as e:
            logger.error("Failed to read local file %s: %s", path, e)
            return 0
        # Resolve "auto" lang by CJK-ratio detection on the file content
        resolved_lang: str = (
            self._resolve_lang(content, "auto") if lang == "auto" else lang
        )
        url = f"file://{path.resolve()}"
        # Python files are stored as code blocks so the code chunker applies.
        is_python = path.suffix == ".py"
        payload: dict[str, Any] = {
            "url": url,
            "title": path.name,
            "lang": resolved_lang,
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
            "content": "" if is_python else content,
            "code_blocks": [content] if is_python else [],
        }
        self._rag_src_dir.mkdir(parents=True, exist_ok=True)
        out = self._make_crawl_filepath(url)
        out.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
        logger.info("saved local file: %s", out.name)
        return 1

    async def crawl(self, targets: list[tuple[str, str]] | None = None) -> None:
        """Crawl all given targets, or config target_urls when targets is None."""
        for url, lang in targets or self._target_urls:
            logger.info("=== start: %s (lang=%s) ===", url, lang)
            try:
                await self.crawl_site(url, lang)
            except (httpx.RequestError, httpx.HTTPStatusError, OSError) as _crawl_err:
                logger.exception("crawl_site failed: %s: %s", url, _crawl_err)
            logger.info("=== done:  %s ===", url)

    def _drain_queue_to_tasks(
        self,
        queue: asyncio.Queue,
        visited: set[str],
        start_url: str,
        hint_lang: str,
        client: httpx.AsyncClient,
        sem: asyncio.Semaphore,
    ) -> set[asyncio.Task]:
        """Dequeue all pending URLs and create fetch tasks for unvisited ones; visited check is safe because no await occurs between check and add."""
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

    async def crawl_site(self, start_url: str, hint_lang: str) -> None:
        """Async BFS crawl within the same origin up to max_depth levels via asyncio.Semaphore concurrency and FIRST_COMPLETED loop."""
        if not validate_url(start_url):
            logger.error("Invalid start URL (must be http/https): %r", start_url)
            return

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

    # ── Private helpers ───────────────────────────────────────────────────────

    def _get_conditional_headers(self, url: str) -> dict[str, str]:
        """Return If-None-Match/If-Modified-Since headers from the cached document."""
        try:
            with SQLiteHelper().open(row_factory=True) as db:
                rows = db.fetchall(
                    "SELECT etag, last_modified FROM documents WHERE url = ?",
                    (url,),
                )
            if rows:
                hdrs: dict[str, str] = {}
                # sqlite3.Row supports subscript access; NULL columns return None
                if rows[0]["etag"]:
                    hdrs["If-None-Match"] = rows[0]["etag"]
                if rows[0]["last_modified"]:
                    hdrs["If-Modified-Since"] = rows[0]["last_modified"]
                return hdrs
        except (sqlite3.OperationalError, sqlite3.DatabaseError) as e:
            logger.debug("DB lookup for conditional headers failed (%s): %s", url, e)
        return {}

    def _make_crawl_filepath(self, url: str) -> Path:
        """Generate an output path in yyyymmddhhmmss-{slug}.txt format."""
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        slug = url_to_slug(url)
        return self._rag_src_dir / f"{ts}-{slug}.txt"

    async def _fetch_html_async(
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

    def _extract_code_blocks(self, soup: BeautifulSoup) -> list[str]:
        """Extract <pre> text blocks and remove them from the DOM."""
        code_blocks: list[str] = []
        for pre in soup.find_all("pre"):
            code = pre.get_text()
            stripped = code.strip()
            if len(stripped) >= self._min_chunk:
                code_blocks.append(stripped)
            pre.decompose()
        return code_blocks

    def _extract_content(self, html: str, url: str) -> tuple[str, str, list[str]]:
        """Return (title, body text, code blocks) extracted from HTML."""
        soup = BeautifulSoup(html, "lxml")
        title = soup.title.get_text(strip=True) if soup.title else urlparse(url).path
        code_blocks = self._extract_code_blocks(soup)
        text = extract_text(soup)
        return title, text, code_blocks

    def _save_crawl_file(
        self,
        url: str,
        title: str,
        lang: str,
        content: str,
        code_blocks: list[str],
        etag: str | None = None,
        last_modified: str | None = None,
    ) -> Path:
        """Save crawl results as JSON to rag-src/yyyymmddhhmmss-{slug}.txt."""
        self._rag_src_dir.mkdir(parents=True, exist_ok=True)
        path = self._make_crawl_filepath(url)
        payload: dict[str, Any] = {
            "url": url,
            "title": title,
            "lang": lang,
            "fetched_at": datetime.now().isoformat(timespec="seconds"),
            "content": content,
            "code_blocks": code_blocks,
        }
        if etag:
            payload["etag"] = etag
        if last_modified:
            payload["last_modified"] = last_modified
        path.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
        logger.info("saved: %s", path.name)
        return path

    async def _fetch_and_extract_async(
        self,
        url: str,
        client: httpx.AsyncClient,
        extra_headers: dict[str, str] | None = None,
    ) -> tuple[str, str, str, list[str], str | None, str | None] | None:
        """Fetch HTML and extract content; returns (html, title, text, code_blocks, etag, last_modified) or None when unavailable or 304."""
        fetch_result = await self._fetch_html_async(url, client, extra_headers)
        if fetch_result is None:
            return None
        html, etag, last_modified = fetch_result
        title, text, code_blocks = self._extract_content(html, url)
        if not text and not code_blocks:
            logger.debug("no content: %s", url)
            return None
        return html, title, text, code_blocks, etag, last_modified

    def _enqueue_links(
        self,
        html: str,
        current_url: str,
        start_url: str,
        depth: int,
        queue: asyncio.Queue,
    ) -> None:
        """Parse links from HTML and put URLs into the BFS queue; nofollow/external filtering applies; dedup happens at dequeue time."""
        if depth >= self._max_depth:
            return
        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            if self._skip_nofollow:
                rel = a.get("rel", [])
                if isinstance(rel, str):
                    rel = rel.split()
                if "nofollow" in rel:
                    continue
            next_url = normalize_url(urljoin(current_url, a["href"]))
            if self._skip_external and not same_origin(next_url, start_url):
                continue
            queue.put_nowait((next_url, depth + 1))

    def _resolve_lang(self, text: str, hint_lang: str) -> str:
        """Determine page language; 'auto' uses CJK-ratio detection with 'en' fallback for short/inconclusive texts; returns a _SUPPORTED_LANGS value."""
        if hint_lang == "auto":
            if len(text) < MIN_TEXT_LENGTH_FOR_DETECTION:
                return "en"
            return detect_lang(text) or "en"
        if len(text) < MIN_TEXT_LENGTH_FOR_DETECTION:
            return hint_lang
        detected = detect_lang(text)
        return detected if detected is not None else hint_lang

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
        """Fetch, extract, save one URL and enqueue its outbound links; semaphore caps concurrency; crawl_delay throttles; ETag/Last-Modified enable 304 skip."""
        async with sem:
            logger.info("[depth=%s] %s", depth, url)
            await asyncio.sleep(self._crawl_delay)

            # Guard: use cached ETag / Last-Modified for conditional GET (304 skip)
            extra_headers = self._get_conditional_headers(url)
            result = await self._fetch_and_extract_async(url, client, extra_headers)
            # Guard: 304 Not Modified or fetch/extraction failure → skip
            if result is None:
                return
            html, title, text, code_blocks, etag, last_modified = result

            resolved_lang: str = self._resolve_lang(text, hint_lang)
            # Guard: skip pages whose detected language is not supported
            if resolved_lang not in _SUPPORTED_LANGS:
                logger.debug("lang=%r not supported: %s", resolved_lang, url)
                return

            self._save_crawl_file(
                url,
                title,
                resolved_lang,
                text,
                code_blocks,
                etag,
                last_modified,
            )
            self._enqueue_links(html, url, start_url, depth, queue)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    parser = argparse.ArgumentParser(
        description="BFS crawler: saves documents to rag-src/yyyymmddhhmmss-{slug}.txt",
    )
    parser.add_argument(
        "--url",
        nargs="+",
        metavar="URL",
        help=(
            "URLs to crawl (multiple allowed; defaults to all target_urls from config)"
        ),
    )
    parser.add_argument(
        "--lang",
        choices=["en", "ja", "auto"],
        default="en",
        help=(
            "Hint language when --url is given (default: en). "
            "'auto' detects per-page language by CJK character ratio."
        ),
    )
    args = parser.parse_args()

    if args.url:
        invalid = [u for u in args.url if not validate_url(u)]
        if invalid:
            parser.error(f"Invalid URLs (must be http/https): {invalid}")

    crawler = WebCrawler()
    targets = [(u, args.lang) for u in args.url] if args.url else None
    asyncio.run(crawler.crawl(targets))


if __name__ == "__main__":
    main()
