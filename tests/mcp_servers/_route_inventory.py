"""tests/mcp_servers/_route_inventory.py — Shared route-inventory assertion.

The invariant enforced here is structural: an MCP FastAPI app may register exactly
one operation-specific execution route, the shared ``POST /v1/call_tool``. Any other
registered ``POST`` is an operation-specific execution route (a direct-route bypass)
and fails the assertion. This helper is reused by one parametrized case per app in
``tests/mcp_servers/test_route_inventory.py`` so that reintroducing a direct route
fails CI uniformly (REQ-007, AC-5).

The helper never imports a production server module; callers pass the built app and
an app-declared set of approved non-execution GET paths so app-specific diagnostics
(e.g. ``read_server.py``'s ``/list_allowed_directories``) do not leak into the shared
assertion.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.routing import APIRoute

# The two diagnostics every MCP app exposes alongside the single execution POST.
DEFAULT_APPROVED_NON_EXECUTION_GET: frozenset[str] = frozenset({"/health", "/v1/tools"})

# The only operation-specific execution route an MCP app may register.
CALL_TOOL_POST: str = "/v1/call_tool"


def _api_routes(app: FastAPI) -> list[APIRoute]:
    """Return the app's ``APIRoute`` entries (excludes mounts, exception handlers)."""
    return [route for route in app.routes if isinstance(route, APIRoute)]


def assert_single_call_tool_post(
    app: FastAPI,
    *,
    label: str = "",
    approved_non_execution_get: set[str] | None = None,
) -> None:
    """Assert ``app`` exposes exactly one ``POST`` (``/v1/call_tool``) and approved GETs.

    Raises :class:`AssertionError` listing any offending POST paths, and any GET path
    outside ``approved_non_execution_get`` (when supplied), so a reintroduced direct
    route fails CI with an actionable message.
    """
    where = label or getattr(app, "title", "app")
    routes = _api_routes(app)

    post_paths = sorted(route.path for route in routes if "POST" in route.methods)
    if post_paths != [CALL_TOOL_POST]:
        raise AssertionError(
            f"{where!r} registers unexpected POST routes {post_paths}; "
            f"expected only {CALL_TOOL_POST}"
        )

    if approved_non_execution_get is not None:
        get_paths = sorted(route.path for route in routes if "GET" in route.methods)
        approved = set(approved_non_execution_get) | set(
            DEFAULT_APPROVED_NON_EXECUTION_GET
        )
        unexpected_get = [path for path in get_paths if path not in approved]
        if unexpected_get:
            raise AssertionError(
                f"{where!r} registers unexpected GET routes {unexpected_get}; "
                f"approved set is {sorted(approved)}"
            )
