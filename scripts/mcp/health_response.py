#!/usr/bin/env python3
"""mcp/health_response.py — Common health response builder for MCP servers.

All MCP servers share the same /health endpoint JSON structure; this module
eliminates duplication of the JSONResponse payload construction.

Usage:
    from mcp.health_response import make_health_response

    @app.get("/health")
    async def health() -> JSONResponse:
        deps = _check_my_deps()
        details = {"service": "my-mcp"}
        return make_health_response(deps, details)
"""

from __future__ import annotations

from fastapi.responses import JSONResponse


def make_health_response(
    deps: dict[str, str],
    details: dict[str, object] | None = None,
) -> JSONResponse:
    """Build a standard MCP /health JSONResponse.

    Args:
        deps: Dependency status dict; empty means healthy, non-empty means degraded.
        details: Optional extra detail fields included in the response body.

    Returns:
        A JSONResponse with status 200 (healthy) or 503 (degraded).
    """
    ready = len(deps) == 0
    return JSONResponse(
        {
            "status": "ok" if ready else "degraded",
            "ready": ready,
            "liveness": True,
            "restart_recommended": False,
            "operator_action_required": not ready,
            "dependencies": deps,
            "details": details or {},
        },
        status_code=200 if ready else 503,
    )
