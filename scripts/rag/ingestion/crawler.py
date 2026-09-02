#!/usr/bin/env python3
"""scripts/rag/ingestion/crawler.py

BFS web crawler that saves extracted text and code blocks to rag-src/.
Entry point: python Crawler.py [--url URL ...] [--lang {en,ja}]

Output: rag-src/{timestamp}-{slug}.json — JSON payload (not plain text).
Fields: url, title, lang, fetched_at, content, code_blocks, etag, last_modified.

Pipeline position: Crawler.py → ChunkSplitter.py → RagIngester.py

Refactored: WebCrawler reduced to thin composition facade delegating to
HttpFetcher, ContentExtractor, LinkDiscovery, LanguageResolver, and
CrawlPersister components.
"""

import argparse
import asyncio
from pathlib import Path

import httpx
from rag.ingestion.content_extractor import ContentExtractor
from rag.ingestion.crawl_persister import CrawlPersister
from rag.ingestion.crawler_utils import (
    parse_target_urls,
    parse_targets_file,
    validate_url,
)
from rag.ingestion.http_fetcher import HttpFetcher
from rag.ingestion.language_resolver import LanguageResolver
from rag.ingestion.link_discovery import LinkDiscovery
from rag.ingestion.orchestrator import CrawlOrchestrator
from shared.config_loader import ConfigLoader
from shared.logger import Logger

logger = Logger(__name__, "/opt/llm/logs/crawl.log")


# ──────────────────────────────────────────────────────────────────────────────
# Crawler class (thin composition facade)
# ──────────────────────────────────────────────────────────────────────────────
class WebCrawler:
    """Thin composition facade: delegates to HttpFetcher, ContentExtractor,
    LinkDiscovery, LanguageResolver, and CrawlPersister components."""

    _USER_AGENT = "Mozilla/5.0 (compatible; RAG-bot/1.0; +local)"
    # Class-level headers shared across all AsyncClient instances
    _HEADERS: dict[str, str] = {
        "User-Agent": _USER_AGENT,
        "Accept-Language": "ja,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Connection": "keep-alive",
    }

    def __init__(self, config: dict | None = None) -> None:
        """Initialize with optional config override and load crawler settings."""
        self.config: dict = config or ConfigLoader().load("crawler.toml")
        cfg: dict = self.config
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
        # DB settings for conditional-header cache lookups (bypasses build_db_config)
        self._rag_db_path: str = str(cfg.get("rag_db_path", ""))
        self._sqlite_timeout: int = int(cfg.get("sqlite_timeout", 30))
        self._sqlite_busy_timeout_ms: int = int(
            cfg.get("sqlite_busy_timeout_ms", 30000)
        )

        # Wire components via constructor injection
        self.http_fetcher = HttpFetcher(self.config)
        self.content_extractor = ContentExtractor(self._min_chunk)
        self.link_discovery = LinkDiscovery(
            skip_nofollow=self._skip_nofollow,
            skip_external=self._skip_external,
            max_depth=self._max_depth,
        )
        self.language_resolver = LanguageResolver()
        self.crawl_persister = CrawlPersister(self.config)
        self.orchestrator = CrawlOrchestrator(
            http_fetcher=self.http_fetcher,
            content_extractor=self.content_extractor,
            link_discovery=self.link_discovery,
            language_resolver=self.language_resolver,
            persister=self.crawl_persister,
            config=self.config,
        )

    # ── Public interface ──────────────────────────────────────────────────────

    def crawl_file(self, path: Path, lang: str) -> int:
        """Save a local file as a crawl result JSON in rag-src/; .py files stored as code blocks; returns 1 on success, 0 on failure."""
        return self.crawl_persister.save(path, lang)

    async def crawl(self, targets: list[tuple[str, str]] | None = None) -> None:
        """Crawl all given targets, or config target_urls when targets is None."""
        for url, lang in targets or self._target_urls:
            logger.info("=== start: %s (lang=%s) ===", url, lang)
            try:
                if url.startswith("file://"):
                    self.crawl_file(Path(url[len("file://") :]), lang)
                else:
                    await self.orchestrator.crawl_site(url, lang)
            except (httpx.RequestError, httpx.HTTPStatusError, OSError) as _crawl_err:
                logger.exception("crawl failed: %s: %s", url, _crawl_err)
            logger.info("=== done:  %s ===", url)


# ──────────────────────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────────────────────
def main() -> None:
    """CLI entry point for BFS web crawling with language detection."""
    parser = argparse.ArgumentParser(
        description="BFS crawler: saves documents to rag-src/yyyymmddhhmmss-{slug}.json",
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
            "Hint language when --url is given (default: en). 'auto' detects per-page language by CJK character ratio."
        ),
    )
    parser.add_argument(
        "--targets-file",
        metavar="PATH",
        help=(
            "Path to a TOML file containing target_urls = [[url, lang], ...] pairs. Mutually exclusive with --url."
        ),
    )
    args = parser.parse_args()

    if args.url and getattr(args, "targets_file", None):
        parser.error("--url and --targets-file are mutually exclusive")

    crawler = WebCrawler()

    if getattr(args, "targets_file", None):
        try:
            targets = parse_targets_file(Path(args.targets_file))
        except FileNotFoundError as e:
            parser.error(f"--targets-file not found: {e}")
        except ValueError as e:
            parser.error(f"--targets-file parse error: {e}")
    elif args.url:
        invalid = [u for u in args.url if not validate_url(u)]
        if invalid:
            parser.error(f"Invalid URLs (must be http/https): {invalid}")
        targets = [(u, args.lang) for u in args.url]
    else:
        targets = None

    asyncio.run(crawler.crawl(targets))


if __name__ == "__main__":
    from shared.config_loader import ConfigLoader

    ConfigLoader.restrict_to("crawler.toml")
    main()
