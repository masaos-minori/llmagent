"""scripts/eventbus/auth.py"""

from __future__ import annotations

import hashlib
import logging
from dataclasses import dataclass
from enum import StrEnum
from typing import Any

from fastapi import Depends, HTTPException, Request
from fastapi.responses import JSONResponse
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
    ADMIN = "admin"


@dataclass(frozen=True)
class Principal:
    """Authenticated identity carrying roles, consumer IDs, topics, and token fingerprint."""

    roles: frozenset[Role]
    allowed_consumer_ids: frozenset[str]  # empty = unrestricted
    allowed_topics: frozenset[str] | None  # None = unrestricted
    token_fingerprint: str  # non-secret identifier for audit logging


# Route-to-role mapping: which roles may access which route category
_ROUTE_ROLE_MAP: dict[str, set[Role]] = {
    "/health": {Role.MONITORING},
    "/publish": {Role.PUBLISHER},
    "/subscribe": {Role.CONSUMER},
    "/events": {Role.CONSUMER},
    "/ack": {Role.CONSUMER},
    "/nack": {Role.CONSUMER},
    "/dlq": {Role.OPERATOR},
    "/dlq/requeue": {Role.OPERATOR},
    "/replay": {Role.OPERATOR},
    "/admin/*": {Role.ADMIN},
}

# Consumer identity allowlist: consumer_id -> set of permitted topics
# Populated from config at startup; empty means any consumer_id is valid for that caller
_CONSUMER_ID_ALLOWLIST: dict[str, set[str]] = {}

# Token-to-consumer mapping: token -> allowed consumer_ids
_TOKEN_CONSUMER_MAP: dict[str, set[str]] = {}

# Token-to-topic mapping: token -> set of permitted topics
_TOKEN_TOPIC_MAP: dict[str, set[str]] = {}

# Token-to-role mapping: token -> set of roles that token is authorized for
_TOKEN_ROLE_MAP: dict[str, set[Role]] = {}

# Per-role token config field -> the single Role it grants
_PER_ROLE_TOKEN_FIELDS: tuple[tuple[str, Role], ...] = (
    ("publisher_token", Role.PUBLISHER),
    ("consumer_token", Role.CONSUMER),
    ("operator_token", Role.OPERATOR),
    ("monitoring_token", Role.MONITORING),
    ("admin_token", Role.ADMIN),
)


def unauthorized_response(detail: str = "Unauthorized") -> JSONResponse:
    """Return a standardized HTTP 401 Unauthorized response."""
    return JSONResponse(
        content={"error": "Unauthorized", "detail": detail},
        status_code=401,
        headers={"WWW-Authenticate": 'Bearer realm="eventbus"'},
    )


def _derive_token_fingerprint(token: str) -> str:
    """Derive a non-secret fingerprint from a raw token value.

    Uses SHA-256 hash prefix to avoid exposing raw token values in logs.
    """
    return hashlib.sha256(token.encode()).hexdigest()[:16]


def _populate_token_maps(config: Any) -> None:
    """Populate _TOKEN_CONSUMER_MAP, _TOKEN_TOPIC_MAP, and _TOKEN_ROLE_MAP from config at startup."""
    global _TOKEN_CONSUMER_MAP, _TOKEN_TOPIC_MAP, _TOKEN_ROLE_MAP

    # Clear existing mappings
    _TOKEN_CONSUMER_MAP.clear()
    _TOKEN_TOPIC_MAP.clear()
    _TOKEN_ROLE_MAP.clear()

    # The shared auth_token grants every role, preserving backward compatibility
    # with the existing single-token deployment model.
    if hasattr(config, "auth_token") and config.auth_token:
        _TOKEN_CONSUMER_MAP[config.auth_token] = set()  # Empty means any consumer_id
        _TOKEN_TOPIC_MAP[config.auth_token] = set()  # Empty means any topic
        _TOKEN_ROLE_MAP[config.auth_token] = set(Role)

    # Each per-role token grants only its own role.
    for field, role in _PER_ROLE_TOKEN_FIELDS:
        token = getattr(config, field, None)
        if token:
            _TOKEN_ROLE_MAP.setdefault(token, set()).add(role)

    # admin_token is a superuser credential: grants every role, same as auth_token.
    admin_token = getattr(config, "admin_token", None)
    if admin_token:
        _TOKEN_ROLE_MAP.setdefault(admin_token, set()).update(Role)


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


async def resolve_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearerDep),
) -> Principal:
    """Resolve a bearer token to a Principal, or raise 401."""
    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": 'Bearer realm="eventbus"'},
        )

    token = credentials.credentials
    config = request.app.state.config

    try:
        get_auth_token(config)  # fail-closed: 500 if unconfigured
    except ValueError:
        raise HTTPException(
            status_code=500, detail="Server misconfiguration: auth_token not configured"
        )

    if token not in _TOKEN_ROLE_MAP:
        logger.warning("Authentication failed: invalid Bearer token")
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing Bearer token",
            headers={"WWW-Authenticate": 'Bearer realm="eventbus"'},
        )

    roles = frozenset(_TOKEN_ROLE_MAP[token])
    allowed_consumer_ids = frozenset(_TOKEN_CONSUMER_MAP.get(token, set()))
    allowed_topics_raw = _TOKEN_TOPIC_MAP.get(token, set())
    allowed_topics: frozenset[str] | None = (
        frozenset(allowed_topics_raw) if allowed_topics_raw else None
    )
    token_fp = _derive_token_fingerprint(token)

    return Principal(
        roles=roles,
        allowed_consumer_ids=allowed_consumer_ids,
        allowed_topics=allowed_topics,
        token_fingerprint=token_fp,
    )


def require_role(role: Role):
    """FastAPI dependency factory: verify caller's principal has the required role."""

    async def _check_role(
        request: Request,
        principal: Principal = Depends(resolve_principal),
    ) -> Principal:
        if role not in principal.roles:
            logger.warning(
                "Authorization failed: requires %s, caller has %s",
                role,
                principal.roles,
            )
            raise HTTPException(
                status_code=403, detail=f"Forbidden: requires {role} role"
            )
        return principal

    return _check_role


async def require_consumer_identity(
    request: Request,
    consumer_id: str = "",
    topics: list[str] | None = None,
    principal: Principal = Depends(resolve_principal),
) -> Principal:
    """FastAPI dependency: verify caller is authorized to use the given consumer_id and topics.

    Returns a Principal object with authorization context for the caller.
    """
    if (
        consumer_id
        and principal.allowed_consumer_ids
        and consumer_id not in principal.allowed_consumer_ids
    ):
        logger.warning(
            "Authorization failed: consumer_id=%s not allowed for this caller",
            consumer_id,
        )
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: consumer_id '{consumer_id}' not allowed",
        )

    if principal.allowed_topics is not None:
        if topics:
            for topic in topics:
                if topic not in principal.allowed_topics:
                    logger.warning(
                        "Authorization failed: topic=%s not allowed for this caller",
                        topic,
                    )
                    raise HTTPException(
                        status_code=403,
                        detail=f"Forbidden: topic '{topic}' not allowed",
                    )

    return principal


def attach_auth_middleware(app: Any) -> None:
    """Register X-Request-Id middleware on a FastAPI app.

    Authentication is delegated to endpoint dependencies via resolve_principal().
    This middleware only injects X-Request-Id into responses.
    """

    from fastapi import (
        Request,  # noqa: F401 — used only as a type annotation on the nested middleware function's parameter below
    )

    async def _request_id_middleware(request: Request, call_next):  # noqa: ANN001,ANN202 — call_next's type is internal to Starlette and not worth importing solely for this annotation
        """Inject X-Request-Id into response headers."""
        req_id = str(__import__("uuid").uuid4())
        request.state.request_id = req_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = req_id
        return response

    app.add_middleware(BaseHTTPMiddleware, dispatch=_request_id_middleware)
