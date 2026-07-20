#!/usr/bin/env python3
"""mcp_servers/web_search/health.py

In-process DuckDuckGo provider health tracking for web-search-mcp.

Dependency direction: mcp_servers.web_search.health → (stdlib only, leaf module)
Import from here:  from mcp_servers.web_search import health

Tracks last success/failure timestamps, the last error type, and a
consecutive-failure counter, and exposes a degraded/healthy determination
that `web_search_server.py`'s `/health` endpoint folds into its response.

No external probing and no persistence: state is purely in-memory and reset
on process restart. `MCPServer.run_http()` calls `uvicorn.run()` with no
`workers=` argument, so the process is single-worker and a module-level
singleton is safe here.

Caveat: because state resets on restart, `/health` may report "healthy"
immediately after a restart that followed a real outage. This is accepted,
out-of-scope behavior (no cross-process/persistent health tracking today).
"""

from __future__ import annotations

import dataclasses
import time

# Consecutive-failure threshold at which the provider is considered degraded.
# Mirrors MCPServer._record_tool_error's _error_threshold = 3 convention
# (scripts/mcp_servers/server.py).
DEGRADED_THRESHOLD: int = 3


@dataclasses.dataclass
class ProviderHealth:
    """Mutable in-process health state for a search provider."""

    provider: str = "duckduckgo"
    last_success_at: float | None = None
    last_failure_at: float | None = None
    last_error_type: str = ""
    consecutive_failures: int = 0


_health = ProviderHealth()


def record_success() -> None:
    """Record a successful provider call: reset the failure streak.

    last_error_type is intentionally left unchanged — it is informational
    (what the most recent error was), only the consecutive-failure counter
    resets on success.
    """
    _health.last_success_at = time.time()
    _health.consecutive_failures = 0


def record_failure(error_type: str) -> None:
    """Record a failed provider call and increment the failure streak."""
    _health.last_failure_at = time.time()
    _health.last_error_type = error_type
    _health.consecutive_failures += 1


def is_degraded() -> bool:
    """Return True if consecutive failures reached DEGRADED_THRESHOLD."""
    return _health.consecutive_failures >= DEGRADED_THRESHOLD


def health_details() -> dict[str, object]:
    """Return a plain dict of current health state for /health reporting."""
    return {
        "provider": _health.provider,
        "last_success_at": _health.last_success_at,
        "last_failure_at": _health.last_failure_at,
        "last_error_type": _health.last_error_type,
        "consecutive_failures": _health.consecutive_failures,
        "degraded": is_degraded(),
    }


def reset() -> None:
    """Reset health state to defaults. Test helper only."""
    global _health
    _health = ProviderHealth()
