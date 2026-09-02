#!/usr/bin/env python3
"""scripts/rag/ingestion/content_extractor.py

ContentExtractor: owns HTML content extraction concern.

Extracted from WebCrawler to separate HTML parsing from BFS orchestration.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from bs4 import BeautifulSoup

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

# Import here to avoid circular imports
from rag.ingestion.crawler_utils import extract_text  # noqa: E402 — local import for circular dependency avoidance


class ContentExtractor:
    """Owns HTML content extraction: title, body text, code blocks."""

    def __init__(self, min_chunk: int = 0) -> None:
        self._min_chunk = min_chunk

    def extract_content(self, html: str, url: str) -> tuple[str, str, list[str]]:
        """Return (title, body text, code blocks) extracted from HTML."""
        soup = BeautifulSoup(html, "lxml")
        title = soup.title.get_text(strip=True) if soup.title else url.split("/")[-1]
        code_blocks = self.extract_code_blocks(soup)
        text = extract_text(soup)
        return title, text, code_blocks

    def extract_code_blocks(self, soup: BeautifulSoup) -> list[str]:
        """Extract <pre> text blocks and remove them from the DOM."""
        code_blocks: list[str] = []
        for pre in soup.find_all("pre"):
            code = pre.get_text()
            stripped = code.strip()
            if len(stripped) >= self._min_chunk:
                code_blocks.append(stripped)
            pre.decompose()
        return code_blocks
