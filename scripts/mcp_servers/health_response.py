#!/usr/bin/env python3
"""scripts/mcp_servers/health_response.py — Common health response builder for MCP servers.

All MCP servers share the same /health endpoint JSON structure; this module
eliminates duplication of the JSONResponse payload construction.

Usage:
    from mcp_servers.health_response import make_health_response

    @app.get("/health")
    async def health() -> JSONResponse:
        deps = _check_my_deps()
        details = {"service": "my-mcp"}
        return make_health_response(deps, details, security=_security_posture)
"""

from __future__ import annotations

import logging
import sqlite3

from fastapi.responses import JSONResponse
from shared.mcp_dedup import collect_dedup_metrics
from shared.security.posture_contract import SecurityPosture

logger = logging.getLogger(__name__)

HEALTH_STATUS_OK = "ok"
HEALTH_STATUS_DEGRADED = "degraded"


def make_health_response(
    deps: dict[str, str],
    details: dict[str, object] | None = None,
    security: SecurityPosture | None = None,
) -> JSONResponse:
    """Build a standard MCP /health JSONResponse.

    Args:
        deps: Dependency status dict; empty means healthy, non-empty means degraded.
        details: Optional extra detail fields included in the response body.
        security: Optional Security Posture the server produced at startup. When supplied, ready
            requires its validated flag and the body carries a security block; when omitted the
            security key is absent, which is how an un-migrated server stays unchanged.

    Returns:
        A JSONResponse with status 200 (healthy) or 503 (degraded).
    """
    ready = len(deps) == 0 and (security is None or security.validated)
    status = HEALTH_STATUS_OK if ready else HEALTH_STATUS_DEGRADED
    status_code = 200 if ready else 503
    payload: dict[str, object] = {
        "status": status,
        "ready": ready,
        "liveness": True,
        "restart_recommended": False,
        "operator_action_required": not ready,
        "dependencies": deps,
        "details": details or {},
    }
    if security is not None:
        payload["security"] = security.to_dict()
    return JSONResponse(payload, status_code=status_code)


def dedup_health_details() -> dict[str, object]:
    """Build the `details.dedup` block for a server's health response (REQ-004).

    The store and config are read through the imported dispatcher module, because a module-level
    name import would capture `None` at import time. The dispatcher import is function-local so
    module import order stays as it is.

    Returns:
        `{"dedup": <metrics payload>}`, or `{}` when there is no store, no config, or the read
        cannot complete. Degradation is silent by design, mirroring `_purge_once`: `/health` never
        fails because the store is busy or broken, and a reported status never gates behaviour (D-6).
        The dict returned is new, so the `details` dict a caller passes to `make_health_response`
        is never mutated and each server's `service` key stays as it is.
    """
    from mcp_servers import dispatch

    store = getattr(dispatch, "_dedup_store", None)
    config = getattr(dispatch, "_dedup_config", None)
    if store is None or config is None:
        return {}
    try:
        return {"dedup": collect_dedup_metrics(store, config)}
    except (sqlite3.Error, OSError) as exc:
        logger.warning("dedup metrics read failed, no dedup block reported: %s", exc)
        return {}
