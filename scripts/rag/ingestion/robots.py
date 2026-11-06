#!/usr/bin/env python3
"""scripts/rag/ingestion/robots.py

RobotsCache: owns per-host robots.txt fetching/parsing and can_fetch answers.

Isolated component for the opt-in robots.txt policy (crawl005). Fetches and parses
``robots.txt`` once per host, caches the parsed ``RobotFileParser``, and answers
``can_fetch(user_agent, url)`` queries so external crawling respects Disallow rules
(REQ-003).
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

logger = logging.getLogger(__name__)


class RobotsCache:
    """Fetches and parses robots.txt per host; answers can_fetch queries."""

    def __init__(self, user_agent: str) -> None:
        self._user_agent = user_agent
        self._parsers: dict[str, RobotFileParser] = {}

    async def fetch_host(self, origin: str, client: httpx.AsyncClient) -> None:
        parsed = urlparse(origin)
        host = parsed.netloc
        if host in self._parsers:
            return
        robots_url = f"{parsed.scheme}://{host}/robots.txt"
        try:
            resp = await client.get(robots_url)
            parser = RobotFileParser()
            if resp.status_code == 200:
                parser.parse(resp.text.splitlines())
            else:
                parser.parse([])
            self._parsers[host] = parser
        except (httpx.RequestError, ValueError):
            fallback = RobotFileParser()
            fallback.parse([])
            self._parsers.setdefault(host, fallback)
            logger.warning("Failed to fetch %s; allowing all", robots_url)

    def is_allowed(self, url: str) -> bool:
        host = urlparse(url).netloc
        parser = self._parsers.get(host)
        if parser is None:
            return True
        return parser.can_fetch(self._user_agent, url)
