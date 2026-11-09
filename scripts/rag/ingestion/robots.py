#!/usr/bin/env python3
"""scripts/rag/ingestion/robots.py — RobotsCache: owns per-host robots.txt fetching/parsing and can_fetch answers.

Isolated component for the opt-in robots.txt policy (crawl005). Fetches and parses
``robots.txt`` once per host, caches the parsed ``RobotFileParser``, and answers
``can_fetch(user_agent, url)`` queries so external crawling respects Disallow rules
(REQ-003).

ragrev014: ``ensure_host`` is the async entry point with an explicit outcome
table (200 parses; 404 and other 4xx except 401/403 allow all; 401/403, 5xx and
network errors disallow all, fail-closed) and a per-request ``follow_redirects``
flag (REQ-004). ``fetch_host`` delegates to it and keeps its signature.
"""

from __future__ import annotations

import logging
from urllib.parse import urlparse
from urllib.robotparser import RobotFileParser

import httpx

logger = logging.getLogger(__name__)

# Statuses whose fetch failure must block the whole host (REQ-001).
_DISALLOW_ALL_STATUSES = frozenset({401, 403})


def _disallow_all_parser() -> RobotFileParser:
    parser = RobotFileParser()
    parser.parse(["User-agent: *", "Disallow: /"])
    return parser


class RobotsCache:
    """Fetches and parses robots.txt per host; answers can_fetch queries."""

    def __init__(self, user_agent: str) -> None:
        self._user_agent = user_agent
        self._parsers: dict[str, RobotFileParser] = {}

    async def ensure_host(self, origin: str, client: httpx.AsyncClient) -> None:
        """Fetch and cache robots.txt for one host at most once (idempotent).

        Outcome table (REQ-001): 200 parses the body; 404 and any other 4xx
        except 401/403 allow all; 401, 403, 5xx and transport errors disallow
        all (fail-closed). A malformed robots.txt (ValueError) keeps the old
        allow-all fallback. No timeout mechanism is added here (REQ-006): the
        caller-supplied client carries the fetch timeout unchanged.
        """
        parsed = urlparse(origin)
        host = parsed.netloc
        if host in self._parsers:
            return
        robots_url = f"{parsed.scheme}://{host}/robots.txt"
        try:
            resp = await client.get(robots_url, follow_redirects=True)
            status = resp.status_code
            if status == 200:
                parser = RobotFileParser()
                parser.parse(resp.text.splitlines())
            elif status in _DISALLOW_ALL_STATUSES or status >= 500:
                parser = _disallow_all_parser()
                logger.warning(
                    "Failed to fetch %s (status %d); disallowing all",
                    robots_url,
                    status,
                )
            else:
                # 404 and other 4xx except 401/403: allow all (unchanged).
                parser = RobotFileParser()
                parser.parse([])
            self._parsers[host] = parser
        except httpx.RequestError as exc:
            self._parsers[host] = _disallow_all_parser()
            logger.warning("Failed to fetch %s (%s); disallowing all", robots_url, exc)
        except ValueError:
            fallback = RobotFileParser()
            fallback.parse([])
            self._parsers.setdefault(host, fallback)
            logger.warning("Failed to parse %s; allowing all", robots_url)

    async def fetch_host(self, origin: str, client: httpx.AsyncClient) -> None:
        await self.ensure_host(origin, client)

    def is_allowed(self, url: str) -> bool:
        host = urlparse(url).netloc
        parser = self._parsers.get(host)
        if parser is None:
            return True
        return parser.can_fetch(self._user_agent, url)
