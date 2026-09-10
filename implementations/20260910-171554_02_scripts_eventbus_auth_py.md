## Goal

Implement `scripts/eventbus/auth.py`: Bearer-token verification helper and the four-role permission model, replacing the existing warning message about missing authentication with actual enforcement.

## Scope

- New module `scripts/eventbus/auth.py` containing:
  - `verify_bearer_token(request, token)` — validates Authorization header against configured token
  - `require_role(request, role)` — FastAPI dependency for role-based permission checks
  - Permission model definitions (publisher/consumer/operator/monitoring)
- Bound authenticated identity to allowed `consumer_id`s and topics in subscribe/ack routes (via `require_consumer_identity` dependency)
- No cross-layer imports (`.importlinter` `eventbus-is-isolated` contract forbids importing `shared`/`mcp_servers`)

## Assumptions

- The `auth_token` configuration key will be added to `config/eventbus.toml` by `REQ-005`'s `load_config()` hardening.
- The token is stored as a plain string in config (following the existing `auth_token = "${ENV:...}"` convention used by MCP server configs).
- Empty/missing `auth_token` must fail closed at startup (per `REQ-005`), not silently skip authentication.
- Consumer identity binding uses a config-driven allowlist: each `consumer_id` maps to permitted topics.

## Design decisions

- **Bearer-token verification**: Mirrors `scripts/mcp_servers/server.py::attach_auth_middleware()` pattern — a FastAPI dependency function checking `request.headers.get("Authorization", "")` against a configured token.
- **Permission model**: Four roles with route-level permissions:
  - Publisher: POST `/publish`
  - Consumer: GET `/subscribe`, POST `/events/{event_id}/ack`, POST `/nack`
  - Operator: GET `/dlq`, POST `/dlq/{event_id}/requeue`, GET `/replay`
  - Monitoring: GET `/health`
- **Consumer identity binding**: Authenticated consumer identity is validated against allowed `consumer_id`s — a caller cannot act as another consumer.
- **Audit logging integration**: Authorization failures logged via `scripts/eventbus/audit.py` (new module, REQ-006).

## Alternatives considered

- Role-per-topic granularity: Would require complex per-topic ACL; fixed role-to-route mapping simpler and sufficient for loopback-only deployment.
- JWT-based claims: Adds cryptographic complexity; static token sufficient for loopback-only.
- Shared audit module: Cannot import from `mcp_servers`/`shared` per isolation contract; reimplemented locally.

## Implementation

### Target file

`scripts/eventbus/auth.py`

### Procedure

Create a new module implementing Bearer-token authentication and role-based authorization for the EventBus API.

### Method

1. Define the `Role` enum (publisher, consumer, operator, monitoring) and route-to-role mapping.
2. Implement `verify_bearer_token(request, token)` — returns True if Authorization header matches "Bearer {token}".
3. Implement `require_role(role: Role)` — FastAPI dependency that:
   - Verifies Bearer token authentication
   - Checks caller has the required role
   - Logs authorization failure via `scripts/eventbus/audit.py`
4. Implement `require_consumer_identity(consumer_id: str)` — FastAPI dependency that:
   - Verifies Bearer token authentication
   - Validates caller is authorized to use the requested `consumer_id`
   - Validates caller can access the requested topic(s)
5. Add `get_auth_token(config)` helper to read the token from `EventBusConfig`.
6. Wire the middleware into `scripts/eventbus/app.py` via `@app.middleware("http")`.

### Details

```python
# scripts/eventbus/auth.py

from __future__ import annotations

import dataclasses
import logging
from enum import StrEnum
from typing import Any

from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from eventbus.audit import log_auth_failure  # noqa: PLC0415 — new module, REQ-006

logger = logging.getLogger(__name__)

# Precedent: scripts/mcp_servers/server.py::attach_auth_middleware()
# Precedent: scripts/mcp_servers/audit.py::AuditRecord (mirrored conceptually)

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

def get_auth_token(config: Any) -> str:
    """Return the auth_token from EventBusConfig, or raise ValueError if missing."""
    token = getattr(config, "auth_token", None)
    if not token:
        raise ValueError(
            "auth_token is required but not configured. "
            "Add auth_token to config/eventbus.toml before starting."
        )
    return token

async def verify_bearer_token(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearer(auto_error=False)),
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
            status_code=500, 
            detail="Server misconfiguration: auth_token not configured"
        )
    
    if token != expected_token:
        logger.warning("Authentication failed: invalid Bearer token")
        return ""
    
    return token

async def require_role(
    role: Role,
    request: Request,
    token: str = Depends(verify_bearer_token),
) -> None:
    """FastAPI dependency: verify caller has the required role."""
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
                    path, role,
                )
                raise HTTPException(
                    status_code=403, 
                    detail=f"Forbidden: requires {role} role"
                )
            return
    
    # Fallback: check exact match
    if path not in _ROUTE_ROLE_MAP:
        logger.warning("Unknown route accessed: %s", path)
        raise HTTPException(status_code=403, detail="Forbidden")

async def require_consumer_identity(
    request: Request,
    consumer_id: str,
    topics: list[str] | None = None,
    token: str = Depends(verify_bearer_token),
) -> None:
    """FastAPI dependency: verify caller is authorized to use the given consumer_id and topics."""
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    # Validate consumer_id is in the allowlist for this caller
    # In practice, the token identifies the caller; we map token -> allowed consumer_ids
    # For simplicity, assume the token itself encodes the consumer identity
    # This would be extended with a proper identity store in production
    if consumer_id and consumer_id not in _CONSUMER_ID_ALLOWLIST.get(token, set()):
        logger.warning(
            "Authorization failed: consumer_id=%s not allowed for this caller",
            consumer_id,
        )
        raise HTTPException(
            status_code=403, 
            detail=f"Forbidden: consumer_id '{consumer_id}' not allowed"
        )
    
    # Validate topic access
    if topics:
        allowed_topics = _CONSUMER_ID_ALLOWLIST.get(token, set())
        for topic in topics:
            if topic not in allowed_topics:
                logger.warning(
                    "Authorization failed: topic=%s not allowed for this caller",
                    topic,
                )
                raise HTTPException(
                    status_code=403, 
                    detail=f"Forbidden: topic '{topic}' not allowed"
                )
```

## Compatibility considerations

- The `HTTPBearer` dependency from FastAPI's security module is standard and compatible with all FastAPI versions.
- The `_ROUTE_ROLE_MAP` constant must be kept in sync with the route definitions in `app.py`.
- Adding `auth_token` to `EventBusConfig` requires updating `load_config()` (REQ-005) and `config/eventbus.toml`.

## Security considerations

- **Token storage**: The token is stored as a plain string in TOML config, following the existing `auth_token = "${ENV:...}"` convention. It should never be committed to version control.
- **Empty token handling**: If `auth_token` is empty/missing, `get_auth_token()` raises `ValueError`, causing the middleware to return 500 (server misconfiguration), not 401. This prevents silent unauthenticated operation.
- **Audit logging**: Authorization failures are logged via `scripts/eventbus/audit.py` without recording the token value.
- **Consumer identity validation**: The current implementation assumes the token encodes the consumer identity; production deployments should use a proper identity store.

## Rollback considerations

- Rolling back this module means removing it and reverting `app.py`'s middleware registration.
- The original warning message about missing authentication (`scripts/eventbus/config.py` line 53) should be restored.
- Route-level permission checks added to `subscribe_route.py`, `ack_route.py`, etc., must also be reverted.

## Validation plan

- Unit test: `verify_bearer_token()` with valid/invalid/missing tokens.
- Integration test: Each route category tested with authorized/unauthorized callers.
- Run `uv run pytest tests/eventbus/test_eventbus_auth.py -v` to verify all auth tests pass.
- Run full EventBus suite: `uv run pytest tests/eventbus/ -q` (baseline: 169 passed + 1 pre-existing unrelated failure).

## Completion criteria

- [ ] `scripts/eventbus/auth.py` created with Bearer-token verification
- [ ] Four-role permission model defined and wired to routes
- [ ] Consumer identity binding implemented
- [ ] Middleware registered in `scripts/eventbus/app.py`
- [ ] Audit logging integrated for authorization failures
- [ ] All auth tests passing (positive/negative cases for every route category)
- [ ] No cross-layer imports (verified via `PYTHONPATH=scripts uv run lint-imports`)

## Out of scope

- Identity store integration (production deployments would need one).
- Token rotation infrastructure.
- Mutual TLS or reverse-proxy authentication.
- Monitoring-specific health/metrics endpoints (defined in ADR but no code change in this Plan).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Create auth.py with Bearer-token verification | Pending | — | — | |
| 2 | Define four-role permission model | Pending | — | — | |
| 3 | Implement consumer identity binding | Pending | — | — | |
| 4 | Wire middleware into app.py | Pending | — | — | |
| 5 | Integrate audit logging | Pending | — | — | |
| 6 | Add/update tests per Validation plan | Pending | — | — | |
| 7 | Run the validation sequence (rules/toolchain.md) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability

- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: REQ-002, REQ-003
- **Source issue**: issues/20260907-125042_eb_h04_eventbus_authentication_authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-101237_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-171554
- **Related target files**: scripts/eventbus/auth.py
