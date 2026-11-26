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
from collections.abc import Mapping, Sequence

from fastapi.responses import JSONResponse
from shared.mcp_dedup import collect_dedup_metrics
from shared.mcp_health_contract import (
    HEALTH_SCHEMA_VERSION,
    CapabilityState,
    parse_health_body,
)
from shared.security.posture_contract import SecurityPosture

logger = logging.getLogger(__name__)

HEALTH_STATUS_OK = "ok"
HEALTH_STATUS_DEGRADED = "degraded"


def make_health_response(
    deps: dict[str, str],
    details: dict[str, object] | None = None,
    security: SecurityPosture | None = None,
    capabilities: Mapping[str, CapabilityState] | None = None,
    degraded_reasons: Sequence[str] | None = None,
) -> JSONResponse:
    """Build a standard MCP /health JSONResponse.

    Args:
        deps: Dependency status dict; empty means healthy, non-empty means degraded.
        details: Optional extra detail fields included in the response body.
        security: Optional Security Posture the server produced at startup. When supplied, ready
            requires its validated flag and the body carries a security block; when omitted the
            security key is absent, which is how an un-migrated server stays unchanged.
        capabilities: Optional capability name to contract state map. When supplied the body
            carries the version-1 capability block; when omitted no new key is written, so the
            body stays a legacy body the Agent reads through the contract's legacy branch (D-6).
        degraded_reasons: Optional reason codes from the contract's closed vocabulary. Read only
            alongside `capabilities`: a legacy body has no reason field.

    Returns:
        A JSONResponse with status 200 (healthy) or 503 (degraded).

    Raises:
        ValueError: A capability state or a reason code is outside the contract vocabulary.
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
    if capabilities is not None:
        # The new fields are written through the contract parser, so the shape this producer
        # emits is the shape the Agent reads and an out-of-vocabulary value fails here rather
        # than at comparison time. Every existing key above is left as it is (REQ-004).
        block = {
            name: {"state": state.state, "reason_code": state.reason_code}
            for name, state in capabilities.items()
        }
        report = parse_health_body(
            {
                "health_schema_version": HEALTH_SCHEMA_VERSION,
                "degraded_reasons": list(degraded_reasons or ()),
                "capabilities": block,
            }
        )
        payload["health_schema_version"] = report.health_schema_version
        payload["degraded_reasons"] = list(report.degraded_reasons)
        payload["capabilities"] = {
            name: {"state": state.state, "reason_code": state.reason_code}
            for name, state in report.capabilities.items()
        }
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
