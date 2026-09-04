#!/usr/bin/env python3
"""scripts/rag/ingestion/link_discovery.py

LinkDiscovery: owns outbound link filtering concern.

Extracted from WebCrawler to separate link discovery from BFS orchestration.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING
from urllib.parse import urljoin

from bs4 import Tag

if TYPE_CHECKING:
    from asyncio import Queue

    from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# Import here to avoid circular imports
from rag.ingestion.crawler_utils import (  # noqa: E402 — local import for circular dependency avoidance
    normalize_url,
    same_origin,
)


class LinkDiscovery:
    """Owns outbound link filtering: nofollow and cross-origin rules."""

    def __init__(
        self,
        skip_nofollow: bool = False,
        skip_external: bool = True,
        max_depth: int = 0,
    ) -> None:
        self._skip_nofollow = skip_nofollow
        self._skip_external = skip_external
        self._max_depth = max_depth

    def enqueue_links(
        self,
        html: str,
        current_url: str,
        start_url: str,
        depth: int,
        queue: Queue[tuple[str, int]],
    ) -> None:
        """Parse links from HTML and put URLs into the BFS queue; nofollow/external filtering applies; dedup happens at dequeue time."""
        if depth >= self._max_depth:
            return
        soup = BeautifulSoup(html, "lxml")
        for a in soup.find_all("a", href=True):
            if not self.should_enqueue_link(a, current_url, start_url):
                continue
            href = str(a["href"])
            next_url = normalize_url(urljoin(current_url, href))
            queue.put_nowait((next_url, depth + 1))

    def should_enqueue_link(self, a_tag: Tag, current_url: str, start_url: str) -> bool:
        """Check if a link should be enqueued based on nofollow and cross-origin rules."""
        href = a_tag.get("href")
        if not isinstance(href, str):
            return False
        if self._skip_nofollow:
            rel = a_tag.get("rel")
            if isinstance(rel, str):
                rel = rel.split()
            if rel and "nofollow" in rel:
                return False
        if self._skip_external:
            next_url = normalize_url(urljoin(current_url, str(href)))
            if not same_origin(next_url, start_url):
                return False
        return True
