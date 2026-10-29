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

from eventbus.audit import log_auth_failure

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
    """Authenticated identity carrying roles, consumer grants, and token fingerprint."""

    roles: frozenset[Role]
    # Explicit (consumer_id, topic) pairs; an empty set is deny-all
    consumer_grants: frozenset[tuple[str, str]]
    token_fingerprint: str  # non-secret identifier for audit logging

    def topics_for(self, consumer_id: str) -> frozenset[str]:
        """Return the topics granted to one consumer_id."""
        return frozenset(t for c, t in self.consumer_grants if c == consumer_id)

    def is_granted(self, consumer_id: str, topic: str) -> bool:
        """Return True when the (consumer_id, topic) pair is granted."""
        return (consumer_id, topic) in self.consumer_grants


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

# Token-to-principal mapping: token -> Principal object
_TOKEN_PRINCIPAL_MAP: dict[str, Principal] = {}

# Roles held by the shared auth_token and the admin_token. Never includes CONSUMER.
_CONTROL_PLANE_ROLES: frozenset[Role] = frozenset(
    {Role.OPERATOR, Role.MONITORING, Role.ADMIN}
)

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


def _build_principal_map(config: Any) -> dict[str, Principal]:
    """Build the token-to-Principal map from config without publishing it.

    Builds the entire map into a fresh local dict. If building raises (e.g.
    consumer_token without consumer_authorization, or a duplicate token), nothing
    has been published and the previous generation stays in force.

    Replaces the old _TOKEN_CONSUMER_MAP / _TOKEN_TOPIC_MAP / _TOKEN_ROLE_MAP
    design with a single Principal-based lookup table.
    """

    # Helper to compute token fingerprint for logging
    def _fingerprint(token: str) -> str:
        import hashlib

        return hashlib.sha256(token.encode()).hexdigest()[:16]

    # Duplicate-non-empty-token guard (REQ-003): reject any two distinct token
    # fields that share a non-empty value before the principal map is built. Name
    # the colliding fields only; never interpolate or log the values.
    seen: dict[str, list[str]] = {}
    for field in (
        "auth_token",
        "publisher_token",
        "consumer_token",
        "operator_token",
        "monitoring_token",
        "admin_token",
    ):
        value = getattr(config, field, None)
        if value:
            seen.setdefault(value, []).append(field)
    for fields in seen.values():
        if len(fields) > 1:
            raise ValueError(
                "eventbus config duplicate token: "
                f"{', '.join(sorted(fields))} share a non-empty value. "
                "Each token field must hold a distinct value."
            )

    # Build the new map into a fresh local dict — do NOT touch _TOKEN_PRINCIPAL_MAP yet.
    new_map: dict[str, Principal] = {}

    # The shared auth_token and admin_token are control-plane credentials: they hold
    # only the Operator, Monitoring, and Admin roles. They never hold the Consumer
    # role (ADR-013 INV-02/INV-07), so no superuser bypasses consumer identity or
    # topic authorization, and they carry no Publisher role either.
    if hasattr(config, "auth_token") and config.auth_token:
        new_map[config.auth_token] = Principal(
            roles=_CONTROL_PLANE_ROLES,
            consumer_grants=frozenset(),
            token_fingerprint=_fingerprint(config.auth_token),
        )

    # consumer_authorization/topic_authorization are expanded into explicit
    # (consumer_id, topic) pairs and granted to the CONSUMER-role token only; the
    # config schema has no per-token consumer_id mapping. A pair is granted when
    # either mapping lists it, so a consumer is never granted another consumer's topic.
    consumer_authorization = getattr(config, "consumer_authorization", None)
    topic_authorization = getattr(config, "topic_authorization", None)

    consumer_token = getattr(config, "consumer_token", None)
    if consumer_token and consumer_authorization is None:
        raise ValueError(
            "consumer_token is configured but consumer_authorization is missing. "
            "Add consumer_authorization to config/eventbus.toml before starting."
        )

    # Both mappings empty yields frozenset() (deny-all), distinct from a missing
    # key, which still raises above.
    pairs: set[tuple[str, str]] = set()
    for consumer_id, consumer_topics in (consumer_authorization or {}).items():
        pairs.update((consumer_id, topic) for topic in consumer_topics)
    for topic, consumer_ids in (topic_authorization or {}).items():
        pairs.update((consumer_id, topic) for consumer_id in consumer_ids)
    consumer_grants = frozenset(pairs)

    # Each per-role token grants only its own role. Grants are attached only to a
    # principal holding the CONSUMER role; any other principal is bound to nothing.
    for field, role in _PER_ROLE_TOKEN_FIELDS:
        token = getattr(config, field, None)
        if not token:
            continue
        new_map[token] = Principal(
            roles=frozenset({role}),
            consumer_grants=consumer_grants if role == Role.CONSUMER else frozenset(),
            token_fingerprint=_fingerprint(token),
        )

    # admin_token holds the same control-plane roles as auth_token and no Consumer role.
    admin_token = getattr(config, "admin_token", None)
    if admin_token:
        new_map[admin_token] = Principal(
            roles=_CONTROL_PLANE_ROLES,
            consumer_grants=frozenset(),
            token_fingerprint=_fingerprint(admin_token),
        )

    return new_map


def _populate_token_maps(config: Any) -> None:
    """Populate _TOKEN_PRINCIPAL_MAP from config at startup.

    Builds the whole map first and publishes it with one assignment through
    publish_principals(), so concurrent readers never observe an empty map window
    and a build error leaves the previous generation in force.
    """
    publish_principals(_build_principal_map(config))


def publish_principals(new_map: dict[str, Principal]) -> None:
    """Atomically publish a fully built principal map.

    Called by ``_populate_token_maps`` after the new map is completely built.
    A single module-level assignment under the GIL ensures concurrent readers
    never observe an empty map window.
    """
    global _TOKEN_PRINCIPAL_MAP
    _TOKEN_PRINCIPAL_MAP = new_map


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

    if token not in _TOKEN_PRINCIPAL_MAP:
        logger.warning("Authentication failed: invalid Bearer token")
        log_auth_failure(
            consumer_id="",
            request_id=request.state.request_id,
            route=request.url.path,
            target="token",
            error_type="authentication_failed",
            detail="",
        )
        raise HTTPException(
            status_code=401,
            detail="Invalid or missing Bearer token",
            headers={"WWW-Authenticate": 'Bearer realm="eventbus"'},
        )

    principal = _TOKEN_PRINCIPAL_MAP[token]
    token_fp = _derive_token_fingerprint(token)

    return Principal(
        roles=principal.roles,
        consumer_grants=principal.consumer_grants,
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
            log_auth_failure(
                consumer_id="",
                request_id=request.state.request_id,
                route=request.url.path,
                target=role.value,
                error_type="authorization_failed",
                detail="",
            )
            raise HTTPException(
                status_code=403, detail=f"Forbidden: requires {role} role"
            )
        return principal

    return _check_role


def authorize_consumer_access(
    request: Request,
    principal: Principal,
    consumer_id: str,
    topics: list[str],
) -> None:
    """Raise HTTP 403 unless every (consumer_id, topic) pair is granted.

    The single authorization decision shared by subscribe, ACK and NACK. No
    principal bypasses it (ADR-013 INV-02, INV-07): a principal must hold the
    CONSUMER role and explicit grants; an empty grant set is deny-all. An empty
    consumer_id is left to the route's own 400, but its topics must still be
    granted to some consumer of the principal.
    """
    if Role.CONSUMER not in principal.roles or not principal.consumer_grants:
        logger.warning("Authorization failed: Consumer-scoped credential required")
        log_auth_failure(
            consumer_id=consumer_id,
            request_id=request.state.request_id,
            route=request.url.path,
            target=consumer_id,
            error_type="consumer_identity_rejected",
            detail="",
        )
        raise HTTPException(
            status_code=403,
            detail="Forbidden: a Consumer-scoped credential is required",
        )

    if consumer_id and not principal.topics_for(consumer_id):
        logger.warning(
            "Authorization failed: consumer_id=%s not allowed for this caller",
            consumer_id,
        )
        log_auth_failure(
            consumer_id=consumer_id,
            request_id=request.state.request_id,
            route=request.url.path,
            target=consumer_id,
            error_type="consumer_identity_rejected",
            detail="",
        )
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: consumer_id '{consumer_id}' not allowed",
        )

    for topic in topics:
        if consumer_id:
            granted = principal.is_granted(consumer_id, topic)
        else:
            granted = any(t == topic for _, t in principal.consumer_grants)
        if not granted:
            logger.warning(
                "Authorization failed: topic=%s not allowed for this caller", topic
            )
            log_auth_failure(
                consumer_id=consumer_id,
                request_id=request.state.request_id,
                route=request.url.path,
                target=topic,
                error_type="topic_authorization_rejected",
                detail="",
            )
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: topic '{topic}' not allowed",
            )


def effective_topics(
    principal: Principal, consumer_id: str, requested: list[str]
) -> list[str]:
    """Return the requested topics, or the consumer's granted topics when none.

    The caller has already passed authorize_consumer_access, so an omitted topic
    list narrows to the grants instead of meaning "all topics".
    """
    if requested:
        return list(requested)
    return sorted(principal.topics_for(consumer_id))


async def require_consumer_identity(
    request: Request,
    consumer_id: str = "",
    topics: list[str] | None = None,
    principal: Principal = Depends(resolve_principal),
) -> Principal:
    """FastAPI dependency: verify caller is authorized for consumer_id and topics."""
    authorize_consumer_access(request, principal, consumer_id, topics or [])
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
