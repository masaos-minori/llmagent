#!/usr/bin/env python3
"""scripts/mcp_servers/server.py

Base class for MCP (Model Context Protocol) servers.
Provides HTTP launch logic shared by all MCP server scripts.

Tool dispatch helpers live in mcp_servers/dispatch.py.
Audit log helpers live in mcp_servers/audit.py.
"""

from __future__ import annotations

import dataclasses
import hmac
import importlib
import json
import logging
import sys
import uuid
from collections.abc import Callable, Sequence
from typing import Any, Protocol

from starlette.requests import Request

from mcp_servers.dispatch import DispatchResult
from mcp_servers.models import McpTool

# Library module: use standard getLogger without a dedicated log file.
logger = logging.getLogger(__name__)

# REQ-004 (mcproute001): shared request-boundary check rejects a keyless
# side-effecting /v1/call_tool before dispatch. The canonical side-effect tool
# set is defined by the sibling issue sideeffect001 as ALL_SIDE_EFFECTING_TOOLS
# in shared.tool_constants. Resolve it defensively: until that set exists the
# boundary is wired in but inert (see the Blocker Log in the implementation
# procedure). importlib+getattr keeps a missing symbol from breaking module
# import and from tripping mypy's import-name check; never add a second
# hardcoded list here.
try:
    _tool_constants = importlib.import_module("shared.tool_constants")
    ALL_SIDE_EFFECTING_TOOLS = getattr(
        _tool_constants, "ALL_SIDE_EFFECTING_TOOLS", None
    )
except ImportError:
    ALL_SIDE_EFFECTING_TOOLS = None


# Type alias for MCP tool argument dictionaries.
# Pydantic models in each server validate the actual structure at runtime.
ToolArgs = dict[str, Any]

# Maximum response size returned to the agent; larger responses are truncated.
MCP_MAX_RESPONSE_BYTES: int = 512 * 1024

# Schema version advertised in each server's /v1/tools response; bump when the
# tool-schema shape changes in a way that matters to Agent-side discovery/validation.
# See TOOL_SCHEMA_V2_FIELDS below for the separate per-tool field set.
MCP_TOOL_SCHEMA_VERSION: str = "1.0"

# Per-tool metadata field names (distinct from the envelope version above):
# every TOOL_LIST entry across all 13 producer modules must declare these
# fields. Schema 2.1 (agentcfg003) keeps the four schema-2.0 names unchanged and
# adds the declared policy fields; the `policy_version` value each entry declares
# is `shared.tool_metadata.TOOL_FIELD_SET_VERSION`, read from that vocabulary
# module. See scripts/shared/resource_scope.py for the validator that enforces
# this contract.
TOOL_SCHEMA_V2_FIELDS: tuple[str, ...] = (
    "is_write",
    "requires_serial",
    "resource_scope_kind",
    "resource_scope_keys",
    "agent_safety_tier",
    "side_effect_class",
    "retry_policy",
    "reconciliation_policy",
    "idempotency_required",
    "preview_capability",
    "policy_version",
)


class _FastAPIApp(Protocol):
    """Minimal FastAPI app interface for middleware attachment."""

    def middleware(self, middleware_type: str) -> Callable[[Callable], Callable]:
        """Attach a middleware function to the FastAPI application."""
        ...


@dataclasses.dataclass(frozen=True)
class TruncationResult:
    """Metadata returned by _truncate_with_meta()."""

    text: str
    truncated: bool
    total_bytes: int
    actual_visible_bytes: int = 0


def _truncate_with_meta(
    text: str, max_bytes: int = MCP_MAX_RESPONSE_BYTES
) -> TruncationResult:
    """Return TruncationResult with truncated text and metadata."""
    encoded = text.encode("utf-8")
    total = len(encoded)
    if total <= max_bytes:
        return TruncationResult(
            text=text, truncated=False, total_bytes=total, actual_visible_bytes=total
        )
    shown = encoded[:max_bytes].decode("utf-8", errors="ignore")
    actual_visible = len(shown.encode("utf-8"))
    truncated_text = (
        shown
        + f"\n[TRUNCATED: {total:,} bytes total, showing {actual_visible:,} bytes]"
    )
    return TruncationResult(
        text=truncated_text,
        truncated=True,
        total_bytes=total,
        actual_visible_bytes=actual_visible,
    )


def attach_auth_middleware(
    app: _FastAPIApp,
    token: str,
) -> None:
    """Register Bearer-token auth + X-Request-Id middleware on a FastAPI app.

    When token is non-empty, requests without a matching Authorization header
    receive a 401 response. An empty token is fail-closed: every request gets
    401, and no accept-all opt-out exists. Production servers refuse to start
    with an empty token — every server module routes its token through
    ``require_auth_token()``, and Agent startup
    (scripts/agent/startup_validation.py) rejects an MCP server configuration
    with an empty auth_token before this middleware would ever run for a real
    Agent-managed server.

    Unlike eventbus.auth.attach_request_id_middleware, which injects only
    X-Request-Id and performs no authentication, this function authenticates a
    Bearer token and fails closed on an empty token.
    """
    from fastapi import Request  # noqa: F401 — used in closure type annotations below
    from fastapi.responses import JSONResponse

    def _is_authorized(request: Request, token: str) -> bool:
        """Return True only when the Bearer header matches a non-empty token."""
        if not token:
            return False
        presented = request.headers.get("Authorization", "")
        return hmac.compare_digest(
            presented.encode("utf-8"), f"Bearer {token}".encode()
        )

    # REQ-004: middleware registered last is outermost and runs first, so the
    # idempotency boundary is registered BEFORE auth and auth is registered LAST.
    # An unauthorized request is therefore rejected by the bearer check before the
    # idempotency boundary ever sees it.
    @app.middleware("http")
    async def _idempotency_key_middleware(  # noqa: ANN001,ANN202 — FastAPI middleware protocol
        request: Request, call_next
    ):
        """Reject a keyless side-effecting POST /v1/call_tool before dispatch (REQ-004).

        Registered before the bearer-auth middleware below, so auth is the
        outermost middleware and runs first; this boundary runs after auth,
        before dispatch. Only governs POST /v1/call_tool. Resolves the
        idempotency key from the same headers/state as extract_request_context().
        Consults the canonical side-effect set from shared.tool_constants; until
        sideeffect001 defines ALL_SIDE_EFFECTING_TOOLS the boundary is inert.
        """
        if request.method != "POST" or request.url.path != "/v1/call_tool":
            return await call_next(request)
        if not ALL_SIDE_EFFECTING_TOOLS:
            return await call_next(request)
        idempotency_key = getattr(
            request.state,
            "idempotency_key",
            request.headers.get("x-idempotency-key", ""),
        )
        if str(idempotency_key).strip():
            # A whitespace-only key counts as missing: it carries no dedup identity.
            return await call_next(request)
        tool_body = await _read_call_tool_body(request)
        tool_name = tool_body.get("name")
        if tool_name in ALL_SIDE_EFFECTING_TOOLS:
            logger.warning(
                "REQ-004 rejected keyless side-effecting /v1/call_tool for %r",
                tool_name,
            )
            return JSONResponse(
                {"error": "side-effecting tool requires X-Idempotency-Key"},
                status_code=422,
            )
        return await call_next(request)

    if not ALL_SIDE_EFFECTING_TOOLS:
        # REQ-004: canonical side-effect set (sideeffect001) not defined yet.
        # Boundary is wired in but inert; log once at startup, enforce nothing.
        logger.warning(
            "REQ-004 idempotency-key boundary inert: "
            "ALL_SIDE_EFFECTING_TOOLS undefined in shared.tool_constants "
            "(define via sideeffect001)"
        )

    @app.middleware("http")
    async def _auth_middleware(request: Request, call_next):  # noqa: ANN001,ANN202 — FastAPI middleware protocol
        """Authenticate requests by validating Bearer token header."""
        req_id = str(uuid.uuid4())
        request.state.request_id = req_id
        if not _is_authorized(request, token):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        response = await call_next(request)
        response.headers["X-Request-Id"] = req_id
        return response


async def _read_call_tool_body(request: Request) -> dict[str, Any]:
    """Return the parsed JSON body of a /v1/call_tool request, or {} on failure.

    Reads (and caches) the request body so downstream handlers still see the
    original payload. Returns {} when the body is empty or not valid JSON.
    """
    try:
        raw = await request.body()
    except Exception:  # noqa: BLE001 — a boundary must never become a 500 vector
        return {}
    if not raw:
        return {}
    try:
        parsed = json.loads(raw)
    except (ValueError, TypeError):
        return {}
    return parsed if isinstance(parsed, dict) else {}


def require_auth_token(label: str, env_var: str, token: str | None) -> str:
    """Return the Bearer token, or refuse to start the server when it is empty.

    Never echoes the token: the message names only the server and the variable.
    """
    if not token:
        raise RuntimeError(
            f"{label}: auth_token is empty; set {env_var} to a non-empty value "
            "(the server does not start without Bearer authentication)"
        )
    return token


def extract_request_context(request: Request) -> tuple[str, str, str]:
    """Extract session_id, request_id, and idempotency_key from request headers/state.

    Returns:
        Tuple of (session_id, request_id, idempotency_key), defaulting to empty string if not present.
    """
    session_id = request.headers.get("x-session-id", "")
    # request_id may be in state (set by middleware) or fall back to header
    request_id = getattr(
        request.state, "request_id", request.headers.get("x-request-id", "")
    )
    # idempotency_key may be in state (set by middleware) or fall back to header
    idempotency_key = getattr(
        request.state, "idempotency_key", request.headers.get("x-idempotency-key", "")
    )
    return session_id, request_id, idempotency_key


class MCPServer:
    """Base class for MCP servers.

    Subclasses declare server_name, server_version, http_host, http_port,
    app_module, and mcp_tools as class attributes, and override dispatch().

    run_http() starts the HTTP server via uvicorn.
    """

    server_name: str  # e.g. "web-search-mcp"
    server_version: str  # e.g. "3.0.0"
    http_host: str = "127.0.0.1"
    http_port: int  # e.g. 8004
    app_module: str  # uvicorn target, e.g. "WebSearchMCPServer:app"
    own_config_file: str = ""  # e.g. "web_search_mcp_server.toml"; set by subclasses
    mcp_tools: list[McpTool]  # tool definitions (retained for subclass reference)

    async def dispatch(self, name: str, args: ToolArgs) -> DispatchResult:
        """Handle a tools/call request. Subclasses must override this."""
        raise NotImplementedError(f"{type(self).__name__}.dispatch is not implemented")

    def _enforce_startup_posture_gate(self) -> None:
        """Refuse to start when the server module's security posture is not validated.

        Resolves `_enforce_posture_gate` from the module named in `app_module` without
        importing a second copy. Under `python -m` and `runpy.run_module(...,
        run_name="__main__")` the running instance is registered as `__main__` rather
        than `mcp_servers.<pkg>.<server>`, so fall back to that instance and register it
        under its real name so uvicorn serves the same single copy. Only modules in the
        `mcp_servers.` namespace are gated, and one that defines no gate fails closed.
        """
        module_name = self.app_module.partition(":")[0]
        if not module_name.startswith("mcp_servers."):
            return
        module = sys.modules.get(module_name)
        if module is None:
            # Running as `python -m` / `runpy.run_module(run_name="__main__")`: the
            # body is registered as __main__, not under its real name. Reuse it so the
            # gate and uvicorn serve one copy instead of re-importing a second.
            module = sys.modules.get("__main__")
        if module is None:
            raise RuntimeError(
                f"{module_name} is not loaded under its real name or as __main__; "
                "cannot enforce the posture gate"
            )
        gate = getattr(module, "_enforce_posture_gate", None)
        if gate is None:
            raise RuntimeError(
                f"{module_name} defines no _enforce_posture_gate; refusing to start"
            )
        sys.modules.setdefault(module_name, module)
        gate()

    def run_http(self) -> None:
        """Launch the HTTP server via uvicorn, enforcing loopback-only binding.

        Also enforces config isolation and the server's security posture gate before
        any socket is created.

        The loopback check, config isolation, and ``_enforce_startup_posture_gate()`` all
        run before the ``try`` below, so a gate ``SystemExit`` intentionally propagates
        uncaught out of ``run_http()`` (fail-fast: the process terminates via the uncaught
        ``SystemExit(1)`` before any socket is created).
        """
        import uvicorn

        if self.http_host not in ("127.0.0.1", "::1"):
            raise ValueError(
                f"{type(self).__name__} bound to non-loopback address "
                f"{self.http_host}. Internal MCP servers must bind to loopback only."
            )

        if self.own_config_file:
            from shared.config_errors import ConfigMissingError
            from shared.config_loader import ConfigLoader

            ConfigLoader.restrict_to(self.own_config_file)
            try:
                own_data = ConfigLoader().load(self.own_config_file)
            except ConfigMissingError:
                own_data = None
        else:
            from shared.config_errors import ConfigPermissionError

            raise ConfigPermissionError(
                "Config Isolation: own_config_file is falsy — "
                "cannot start without config isolation"
            )

        # Dedup bootstrap (mcpdl003 REQ-001/REQ-006): validate this server's own
        # [dedup] table and inject it (and the declared retry_policy of its own
        # tools) before the posture gate and before any socket exists. Typed
        # config errors propagate fail-fast; an unconfigured dispatcher would
        # otherwise degrade to overlay-only mid-service. A missing own config
        # file (test fixture servers) leaves the dispatcher unconfigured, which
        # fails side-effecting calls closed in dispatch.
        from shared.mcp_dedup import load_dedup_section

        from mcp_servers.dispatch import configure_dedup, configure_tool_retry_policies

        if own_data is not None:
            configure_dedup(
                load_dedup_section(own_data.get("dedup"), self.own_config_file)
            )
        else:
            logger.warning(
                "event=dedup_bootstrap_missing_config server=%s config=%s — "
                "dedup left unconfigured",
                self.server_name,
                self.own_config_file,
            )
        configure_tool_retry_policies(getattr(self, "mcp_tools", ()))

        self._enforce_startup_posture_gate()

        class _LoopbackVerifyingServer(uvicorn.Server):
            """Post-start verification that runs after ``super().startup()`` has
            created the listening sockets; it returns early when
            ``self.should_exit`` is set or ``self.servers`` is empty. This is
            defense-in-depth only: the pre-bind ``http_host`` allow-list above is
            the authoritative guard that loopback binding was validated against."""

            async def startup(self, sockets: list[Any] | None = None) -> None:
                await super().startup(sockets=sockets)
                if self.should_exit or not getattr(self, "servers", None):
                    return
                for srv in self.servers:
                    for sock in srv.sockets or []:
                        bound_host = sock.getsockname()[0]
                        if bound_host not in ("127.0.0.1", "::1"):
                            raise RuntimeError(
                                "Post-start verification failed: bound socket "
                                f"address is {bound_host!r}, not loopback."
                            )

        config = uvicorn.Config(
            self.app_module,
            host=self.http_host,
            port=self.http_port,
            log_level="info",
        )
        server = _LoopbackVerifyingServer(config=config)
        try:
            server.run()
        except SystemExit as e:  # noqa: BLE001 — SystemExit originating from server.run() itself; logged and re-raised, with the sys.exit(1) follow-up below
            logging.getLogger(type(self).__name__).error(
                "server.run() exited with SystemExit: %s", e
            )
            raise
        except KeyboardInterrupt:  # pragma: no cover — interactive-only path
            pass
        if not server.started:
            sys.exit(1)


def build_tools_response(
    tools: Sequence[McpTool],
    server_key: str,
    *,
    include_disabled: bool = False,
    disabled_code: str | None = None,
) -> dict[str, Any]:
    """Build the /v1/tools response dict: schema_version + per-tool server_key tagging.

    Callable directly from each server's module-level FastAPI route handler (no MCPServer
    instance required) — see docstring on MCP_TOOL_SCHEMA_VERSION for the versioning contract.

    Args:
        tools: Tool definitions from the server's TOOL_LIST.
        server_key: Server identifier to tag each tool with.
        include_disabled: When True, include tools even if they are disabled.
        disabled_code: When provided, further filter to only tools matching that code.

    Returns:
        Response dict with schema_version and tools list.
    """
    result: list[dict[str, Any]] = []
    for t in tools:
        tool_dict: dict[str, Any] = {**t, "server_key": server_key}
        # Apply visibility filtering based on annotation fields
        if not include_disabled:
            if tool_dict.get("enabled", True) is False:
                continue
        if disabled_code is not None:
            if tool_dict.get("disabled_reason") != disabled_code and tool_dict.get(
                "enabled", True
            ):
                continue
        result.append(tool_dict)
    return {
        "schema_version": MCP_TOOL_SCHEMA_VERSION,
        "tools": result,
    }
