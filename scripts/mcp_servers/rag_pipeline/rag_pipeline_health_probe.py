#!/usr/bin/env python3
"""scripts/mcp_servers/rag_pipeline/rag_pipeline_health_probe.py — bounded, cached embed_url probe

Reachability probe for the embedding service configured as embed_url, so rag-pipeline-mcp's
/health can report a configured-but-unreachable embedding service instead of only reporting the
key as absent.

Held in its own module rather than in rag_pipeline_server.py so the HTTP transport, the timeout
budget, and the short-TTL cache are testable without the FastAPI application, and so the server
module stays under the module-size gate.

Dependency direction: rag_pipeline_server -> rag_pipeline_health_probe
"""

from __future__ import annotations

import asyncio
import time
from typing import Any, Final

import httpx

PROBE_TIMEOUT_SECONDS: Final[float] = 2.0
CACHE_TTL_SECONDS: Final[float] = 5.0

STATE_REACHABLE: Final[str] = "reachable"
STATE_UNREACHABLE: Final[str] = "unreachable"

# Keyed by the embed base URL; value is (state, monotonic time the state was recorded).
_CACHE: dict[str, tuple[str, float]] = {}


def reset_cache() -> None:
    """Drop every cached probe result."""
    _CACHE.clear()


def _health_url(base: str) -> str:
    return f"{base}/health"


async def _get(caller: Any, url: str, timeout: float) -> int:
    # A stub or hung transport may ignore the timeout argument, so the budget is
    # enforced here as well and not left to the HTTP client alone.
    if caller is not None:
        resp = await asyncio.wait_for(caller.get(url, timeout=timeout), timeout)
        return int(resp.status_code)
    async with httpx.AsyncClient() as client:
        resp = await asyncio.wait_for(client.get(url, timeout=timeout), timeout)
        return int(resp.status_code)


async def _run_probe(base: str, caller: Any, timeout: float) -> str:
    try:
        status = await _get(caller, _health_url(base), timeout)
    except (httpx.HTTPError, OSError, TimeoutError):
        return STATE_UNREACHABLE
    return STATE_REACHABLE if status == httpx.codes.OK else STATE_UNREACHABLE


async def probe_embed_reachable(
    embed_url: str,
    *,
    caller: Any = None,
    timeout: float = PROBE_TIMEOUT_SECONDS,
) -> str:
    """Return "reachable" when GET <embed_url>/health answers 200, else "unreachable".

    A transport error, a timeout, or a non-200 answer all resolve to "unreachable"; the
    function never raises for them. A result younger than CACHE_TTL_SECONDS is returned
    without issuing a request. caller is an object with an async get(url, timeout=...).
    """
    base = embed_url.rstrip("/")
    now = time.monotonic()
    cached = _CACHE.get(base)
    if cached is not None and now - cached[1] < CACHE_TTL_SECONDS:
        return cached[0]
    state = await _run_probe(base, caller, timeout)
    _CACHE[base] = (state, now)
    return state
