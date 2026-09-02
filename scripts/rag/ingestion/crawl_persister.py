#!/usr/bin/env python3
"""scripts/rag/ingestion/crawl_persister.py

CrawlPersister: owns JSON payload construction and write concern.

Extracted from WebCrawler to separate persistence from BFS orchestration.
"""

from __future__ import annotations

import hashlib
import logging
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING

import orjson

if TYPE_CHECKING:
    from rag.ingestion.pipeline_utils import CrawlJsonPayload

logger = logging.getLogger(__name__)

# Import here to avoid circular imports
from rag.ingestion.crawler_utils import url_to_slug  # noqa: E402 — local import for circular dependency avoidance


class CrawlPersister:
    """Owns JSON payload construction and write to rag-src/."""

    def __init__(self, config: dict) -> None:
        self._rag_src_dir: Path = Path(config.get("rag_src_dir", "rag-src"))
        # Re-import here to avoid circular imports
        from rag.ingestion.pipeline_utils import CrawlJsonPayload

        self.CrawlJsonPayload = CrawlJsonPayload

    def save(
        self,
        path: Path,
        lang: str,
    ) -> int:
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
        resolved_lang: str = lang if lang != "auto" else lang
        if resolved_lang not in frozenset({"en", "ja"}):
            logger.warning(
                "lang=%r not supported, skipping local file: %s", resolved_lang, path
            )
            return 0
        url = f"file://{path.resolve()}"
        # Compute mtime and SHA-256 for freshness detection in ingester
        stat = path.stat()
        mtime_utc = datetime.fromtimestamp(stat.st_mtime, tz=UTC).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        sha256 = hashlib.sha256(content.encode("utf-8", errors="ignore")).hexdigest()
        # Python files are stored as code blocks so the code chunker applies.
        is_python = path.suffix == ".py"
        payload: CrawlJsonPayload = {
            "url": url,
            "title": path.name,
            "lang": resolved_lang,
            "fetched_at": mtime_utc,
            "content": "" if is_python else content,
            "code_blocks": [content] if is_python else [],
            "etag": sha256,
            "last_modified": mtime_utc,
        }
        self._rag_src_dir.mkdir(parents=True, exist_ok=True)
        out = self.make_crawl_filepath(url)
        out.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
        logger.info(
            "saved local file",
            extra={"url": url, "source_type": "file"},
        )
        return 1

    def make_crawl_filepath(self, url: str) -> Path:
        """Generate an output path in yyyymmddhhmmss-{slug}.json format."""
        ts = datetime.now().strftime("%Y%m%d%H%M%S")
        slug = url_to_slug(url)
        return self._rag_src_dir / f"{ts}-{slug}.json"

    def save_http(
        self,
        url: str,
        title: str,
        lang: str,
        content: str,
        code_blocks: list[str],
        etag: str | None = None,
        last_modified: str | None = None,
        fetched_at: str | None = None,
    ) -> Path:
        """Save crawl results as JSON to rag-src/yyyymmddhhmmss-{slug}.json."""
        if lang not in frozenset({"en", "ja"}):
            logger.warning("lang=%r not supported, skipping save: %s", lang, url)
            return self.make_crawl_filepath(url)
        if not isinstance(code_blocks, list):
            logger.warning("code_blocks is not a list, skipping save: %s", url)
            return self.make_crawl_filepath(url)
        if not content and not code_blocks:
            logger.warning("empty content without code blocks, skipping save: %s", url)
            return self.make_crawl_filepath(url)
        self._rag_src_dir.mkdir(parents=True, exist_ok=True)
        path = self.make_crawl_filepath(url)
        payload: CrawlJsonPayload = {
            "url": url,
            "title": title,
            "lang": lang,
            "fetched_at": fetched_at
            or datetime.now(UTC).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "content": content,
            "code_blocks": code_blocks,
            "etag": etag,
            "last_modified": last_modified,
        }
        path.write_bytes(orjson.dumps(payload, option=orjson.OPT_INDENT_2))
        logger.info(
            "saved",
            extra={"url": url, "source_type": "http"},
        )
        return path
