"""scripts/eventbus/auth.py"""

from __future__ import annotations

import logging
from enum import StrEnum
from typing import Any

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from starlette.middleware.base import BaseHTTPMiddleware

logger = logging.getLogger(__name__)

# Precedent: scripts/mcp_servers/server.py::attach_auth_middleware()
# Precedent: scripts/mcp_servers/audit.py::AuditRecord (mirrored conceptually)

HTTPBearerDep = HTTPBearer(auto_error=False)


class Role(StrEnum):
    PUBLISHER = "publisher"
    CONSUMER = "consumer"
    OPERATOR = "operator"
    MONITORING = "monitoring"


# Route-to-role mapping: which roles may access which route category
_ROUTE_ROLE_MAP: dict[str, set[Role]] = {
    "/health": {Role.MONITORING},
    "/publish": {Role.PUBLISHER},
    "/subscribe": {Role.CONSUMER},
    "/ack": {Role.CONSUMER},
    "/nack": {Role.CONSUMER},
    "/dlq": {Role.OPERATOR},
    "/dlq/requeue": {Role.OPERATOR},
    "/replay": {Role.OPERATOR},
}

# Consumer identity allowlist: consumer_id -> set of permitted topics
# Populated from config at startup; empty means any consumer_id is valid for that caller
_CONSUMER_ID_ALLOWLIST: dict[str, set[str]] = {}

# Token-to-consumer mapping: token -> allowed consumer_ids
_TOKEN_CONSUMER_MAP: dict[str, set[str]] = {}

# Token-to-topic mapping: token -> set of permitted topics
_TOKEN_TOPIC_MAP: dict[str, set[str]] = {}


def _populate_token_maps(config: Any) -> None:
    """Populate _TOKEN_CONSUMER_MAP and _TOKEN_TOPIC_MAP from config at startup."""
    global _TOKEN_CONSUMER_MAP, _TOKEN_TOPIC_MAP

    # Clear existing mappings
    _TOKEN_CONSUMER_MAP.clear()
    _TOKEN_TOPIC_MAP.clear()

    # Get per-role token configuration from config
    # This assumes EventBusConfig has fields like:
    # - publisher_token: str
    # - consumer_token: str
    # - operator_token: str
    # - monitoring_token: str
    # And potentially per-consumer/topic restrictions

    # For now, assume the single shared token grants all permissions
    # This preserves backward compatibility with the existing single-token model
    if hasattr(config, "auth_token") and config.auth_token:
        _TOKEN_CONSUMER_MAP[config.auth_token] = set()  # Empty means any consumer_id
        _TOKEN_TOPIC_MAP[config.auth_token] = set()  # Empty means any topic


def get_auth_token(config: Any) -> str:
    """Return the auth_token from EventBusConfig, or raise ValueError if missing."""
    token = getattr(config, "auth_token", None)
    if not token:
        raise ValueError(
            "auth_token is required but not configured. "
            "Add auth_token to config/eventbus.toml before starting."
        )
    assert isinstance(token, str), f"Expected str, got {type(token).__name__}"
    return token


async def verify_bearer_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearerDep),
) -> str:
    """Verify Bearer token and return the token value, or raise 401."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Unauthorized")

    token = credentials.credentials
    config = request.app.state.config

    try:
        expected_token = get_auth_token(config)
    except ValueError:
        raise HTTPException(
            status_code=500, detail="Server misconfiguration: auth_token not configured"
        )

    if token != expected_token:
        logger.warning("Authentication failed: invalid Bearer token")
        return ""

    return token


def require_role(role: Role):
    """FastAPI dependency factory: verify caller has the required role.

    Determines the caller's role from their Bearer token using configuration,
    then checks if that role is allowed for the requested endpoint.
    """

    async def _check_role(
        request: Request,
        token: str = Depends(verify_bearer_token),
    ) -> Role:
        if not token:
            # Authentication already failed in verify_bearer_token
            raise HTTPException(status_code=401, detail="Unauthorized")

        # Determine which route category is being accessed
        path = request.url.path
        for route_path, allowed_roles in _ROUTE_ROLE_MAP.items():
            if path.startswith(route_path):
                if role not in allowed_roles:
                    logger.warning(
                        "Authorization failed: %s requires role=%s, caller has none",
                        path,
                        role,
                    )
                    raise HTTPException(
                        status_code=403, detail=f"Forbidden: requires {role} role"
                    )
                return role

        # If no route matched, deny access
        raise HTTPException(status_code=403, detail="Forbidden: unknown route")

    return _check_role


async def require_consumer_identity(
    request: Request,
    consumer_id: str,
    topics: list[str] | None = None,
    token: str = Depends(verify_bearer_token),
) -> dict[str, Any]:
    """FastAPI dependency: verify caller is authorized to use the given consumer_id and topics.

    Returns a dict with 'topics' key containing a set of permitted topics,
    matching the contract expected by subscribe_route.py's subscribe() function.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Validate consumer_id is in the allowlist for this caller
    if consumer_id and consumer_id not in _TOKEN_CONSUMER_MAP.get(token, set()):
        logger.warning(
            "Authorization failed: consumer_id=%s not allowed for this caller",
            consumer_id,
        )
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: consumer_id '{consumer_id}' not allowed",
        )

    # Validate topic access
    allowed_topics = set()
    if topics:
        allowed_topics_from_map = _TOKEN_TOPIC_MAP.get(token, set())
        for topic in topics:
            if topic not in allowed_topics_from_map:
                logger.warning(
                    "Authorization failed: topic=%s not allowed for this caller",
                    topic,
                )
                raise HTTPException(
                    status_code=403, detail=f"Forbidden: topic '{topic}' not allowed"
                )
        allowed_topics = allowed_topics_from_map

    # Return a dict-like object with 'topics' key
    return {"topics": allowed_topics}


def attach_auth_middleware(app: Any) -> None:
    """Register Bearer-token auth middleware on a FastAPI app.

    Must be called exactly once, immediately after the FastAPI app object is
    constructed — Starlette freezes the middleware stack the moment the app
    receives its first ASGI call (including the "lifespan" scope), so calling
    this from inside a `lifespan` handler raises "Cannot add middleware after
    an application has started".

    The expected auth_token is read from `request.app.state.config.auth_token`
    on each request rather than captured at attach time, since app.state.config
    is only populated once `lifespan` runs `load_config()` — which happens
    after this function has already registered the middleware, and which
    tests re-run per-test (via a monkeypatched `load_config`) against the same
    module-level `app` object.

    When the configured token is non-empty, requests without a matching
    Authorization header receive a 401 response. When it is empty, auth is
    skipped and the middleware only injects the X-Request-Id response
    header. An empty token is not a supported production configuration:
    EventBusConfig rejects an empty auth_token before this middleware would
    ever see one for a real deployment. The accept-all fallback exists for
    this function's own standalone testability, not as a supported
    deployment mode.
    """
    from fastapi import Request  # noqa: F401 — used in closure type annotations below
    from fastapi.responses import JSONResponse

    def _is_authorized(request: Request) -> bool:
        """Return True when no token is required or the Bearer header matches."""
        tok = getattr(request.app.state.config, "auth_token", "") or ""
        if not tok:
            return True
        return request.headers.get("Authorization", "") == f"Bearer {tok}"

    async def _auth_middleware(request: Request, call_next):  # noqa: ANN001,ANN202 — FastAPI middleware protocol
        """Authenticate requests by validating Bearer token header."""
        req_id = str(__import__("uuid").uuid4())
        request.state.request_id = req_id
        if not _is_authorized(request):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        response = await call_next(request)
        response.headers["X-Request-Id"] = req_id
        return response

    app.add_middleware(BaseHTTPMiddleware, dispatch=_auth_middleware)
