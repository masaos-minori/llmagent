# Implementation Procedure: Consolidate credential resolution into principal-based authentication

## Goal

Replace the split authentication design (middleware checking `auth_token` separately from endpoint dependencies checking per-role tokens) with a single typed `Principal` object that carries resolved identity through every endpoint's authorization decision.

## Scope

- Introduce `Principal` dataclass in `scripts/eventbus/auth.py`.
- Replace `verify_bearer_token()` with `resolve_principal()`.
- Replace `require_role()` with principal-aware version using `Depends(resolve_principal)`.
- Replace `require_consumer_identity()` to use `Principal` fields directly.
- Update middleware to delegate authentication to endpoint dependencies while preserving `X-Request-Id` injection.
- Wire `Principal` through `scripts/eventbus/app.py` endpoint dependencies.

## Assumptions

- A: The `Role` enum values in `scripts/eventbus/auth.py` are the canonical set of roles for the EventBus process.
- B: Per-role tokens map one-to-one with roles (publisher_token → PUBLISHER, etc.) — this mapping is already defined in `_PER_ROLE_TOKEN_FIELDS`.
- C: The shared `auth_token` grants all roles for backward compatibility — this convention is already implemented in `_populate_token_maps()` line 77.
- D: `admin_token` is a superuser credential granting all roles — confirmed by `_populate_token_maps()` line 87-88.
- E: The middleware's `X-Request-Id` injection behavior should be preserved during refactoring.

## Design decisions

- **Single authentication authority**: Endpoint dependencies (`require_role`, `require_consumer_identity`) become the sole authentication authority. The middleware continues injecting `X-Request-Id` but delegates authentication to endpoint dependencies.
- **Principal dataclass**: Frozen dataclass carrying resolved identity (roles, consumer IDs, topics, token fingerprint).
- **Token fingerprint**: Non-secret identifier for audit logging, derived from SHA-256 prefix of the token.
- **String-prefix route authorization removal**: Replace with FastAPI-native route metadata (route name or path template).

## Alternatives considered

- **Middleware as sole authority**: Keep the middleware as the authentication check point and have endpoint dependencies only verify roles. This was rejected because the middleware currently checks `auth_token` only — it cannot validate per-role tokens. Endpoint dependencies already check per-role tokens via `_TOKEN_ROLE_MAP`, so consolidating there eliminates the split where middleware accepts a request that an endpoint dependency would reject.
- **Keep both authorities**: Maintain both middleware and endpoint dependency checks with explicit coordination. This adds complexity without security benefit — the split design is the root cause of inconsistent authorization conclusions.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters (`since_seq`, `consumer_id`, `Last-Event-ID`) remain unchanged.
- The SSE response format (`id:`, `data:` fields) remains unchanged.
- The `replay_ceil` variable scope and lifecycle remain unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 (unknown/missing token) or HTTP 403 (insufficient roles), never HTTP 500.
- The `resolve_principal()` function must raise HTTP 401 for unknown/missing tokens before any authorization check occurs.

## Rollback considerations

- If the principal model introduces regressions, reverting requires restoring the original `verify_bearer_token()`, `require_role()`, and `require_consumer_identity()` functions.
- The revert is mechanical — no semantic changes to rollback beyond restoring original function signatures.

## Implementation

### Target file

`scripts/eventbus/auth.py`

### Procedure

#### Step 1: Introduce Principal dataclass (REQ-001)

Add the `Principal` dataclass after the `Role` enum definition:

```python
from dataclasses import dataclass

@dataclass(frozen=True)
class Principal:
    """Authenticated identity carrying roles, consumer IDs, topics, and token fingerprint."""
    roles: frozenset[Role]
    allowed_consumer_ids: frozenset[str]  # empty = unrestricted
    allowed_topics: frozenset[str] | None  # None = unrestricted
    token_fingerprint: str  # non-secret identifier for audit logging
```

#### Step 2: Add token fingerprint derivation (REQ-001)

Add a helper function to derive a non-secret fingerprint from a raw token:

```python
def _derive_token_fingerprint(token: str) -> str:
    """Derive a non-secret fingerprint from a raw token value.
    
    Uses SHA-256 hash prefix to avoid exposing raw token values in logs.
    """
    import hashlib
    return hashlib.sha256(token.encode()).hexdigest()[:16]
```

#### Step 3: Update `_populate_token_maps()` to populate principal fields (REQ-006)

Modify `_populate_token_maps()` to also populate principal-related fields. Currently it populates `_TOKEN_CONSUMER_MAP`, `_TOKEN_TOPIC_MAP`, and `_TOKEN_ROLE_MAP`. We need to add principal field population:

Current code (lines 63-88):
```python
def _populate_token_maps(config: Any) -> None:
    global _TOKEN_CONSUMER_MAP, _TOKEN_TOPIC_MAP, _TOKEN_ROLE_MAP
    ...
```

New code:
```python
def _populate_token_maps(config: Any) -> None:
    global _TOKEN_CONSUMER_MAP, _TOKEN_TOPIC_MAP, _TOKEN_ROLE_MAP
    
    # Clear existing mappings
    _TOKEN_CONSUMER_MAP.clear()
    _TOKEN_TOPIC_MAP.clear()
    _TOKEN_ROLE_MAP.clear()
    
    # The shared auth_token grants every role, preserving backward compatibility
    if hasattr(config, "auth_token") and config.auth_token:
        _TOKEN_CONSUMER_MAP[config.auth_token] = set()
        _TOKEN_TOPIC_MAP[config.auth_token] = set()
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
```

No structural change needed here — the current mapping logic is correct. The principal fields will be populated inline in `resolve_principal()` rather than pre-populated globally, which avoids stale state issues.

#### Step 4: Replace `verify_bearer_token()` with `resolve_principal()` (REQ-002, REQ-004)

Replace the current `verify_bearer_token()` function (lines 103-125):

Current code:
```python
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
        get_auth_token(config)  # fail-closed: 500 if unconfigured
    except ValueError:
        raise HTTPException(
            status_code=500, detail="Server misconfiguration: auth_token not configured"
        )
    
    if token not in _TOKEN_ROLE_MAP:
        logger.warning("Authentication failed: invalid Bearer token")
        return ""
    
    return token
```

New code:
```python
async def resolve_principal(
    request: Request,
    credentials: HTTPAuthorizationCredentials = Depends(HTTPBearerDep),
) -> Principal:
    """Resolve a bearer token to a Principal, or raise 401."""
    if credentials is None:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
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
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    roles = frozenset(_TOKEN_ROLE_MAP[token])
    allowed_consumer_ids = frozenset(_TOKEN_CONSUMER_MAP.get(token, set()))
    allowed_topics_raw = _TOKEN_TOPIC_MAP.get(token, set())
    allowed_topics: frozenset[str] | None = frozenset(allowed_topics_raw) if allowed_topics_raw else None
    token_fp = _derive_token_fingerprint(token)
    
    return Principal(
        roles=roles,
        allowed_consumer_ids=allowed_consumer_ids,
        allowed_topics=allowed_topics,
        token_fingerprint=token_fp,
    )
```

Key changes:
- Returns `Principal` instead of raw token string
- Raises HTTP 401 for unknown tokens (instead of returning empty string)
- Derives token fingerprint for audit logging
- Populates principal fields from existing token maps

#### Step 5: Replace `require_role()` with principal-aware version (REQ-003, REQ-004, REQ-009, REQ-010)

Replace the current `require_role()` function (lines 128-172):

Current code:
```python
def require_role(role: Role):
    async def _check_role(
        request: Request,
        token: str = Depends(verify_bearer_token),
    ) -> Role:
        if not token:
            raise HTTPException(status_code=401, detail="Unauthorized")
        
        caller_roles = _TOKEN_ROLE_MAP.get(token, set())
        if role not in caller_roles:
            logger.warning(...)
            raise HTTPException(status_code=403, detail=f"Forbidden: requires {role} role")
        
        # String-prefix route matching (to be removed)
        path = request.url.path
        for route_path, allowed_roles in _ROUTE_ROLE_MAP.items():
            if path.startswith(route_path):
                if role not in allowed_roles:
                    logger.warning(...)
                    raise HTTPException(status_code=403, detail=f"Forbidden: requires {role} role")
                return role
        
        raise HTTPException(status_code=403, detail="Forbidden: unknown route")
    
    return _check_role
```

New code:
```python
def require_role(role: Role):
    """FastAPI dependency factory: verify caller's principal has the required role."""
    async def _check_role(
        request: Request,
        principal: Principal = Depends(resolve_principal),
    ) -> Principal:
        if role not in principal.roles:
            logger.warning(
                "Authorization failed: requires %s, caller has %s",
                role, principal.roles,
            )
            raise HTTPException(status_code=403, detail=f"Forbidden: requires {role} role")
        return principal
    
    return _check_role
```

Key changes:
- Uses `Depends(resolve_principal)` instead of `Depends(verify_bearer_token)` — principal resolved once
- Compares against `principal.roles` instead of `_TOKEN_ROLE_MAP.get(token, set())`
- Removes string-prefix route matching (REQ-009, REQ-010)
- Always returns HTTP 403 for insufficient roles (never 401, since auth was already validated by `resolve_principal`)
- Returns `Principal` instead of `Role`

#### Step 6: Replace `require_consumer_identity()` to use Principal fields directly (REQ-003)

Replace the current `require_consumer_identity()` function (lines 175-229):

Current code:
```python
async def require_consumer_identity(
    request: Request,
    consumer_id: str = "",
    topics: list[str] | None = None,
    token: str = Depends(verify_bearer_token),
) -> dict[str, Any]:
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")
    
    allowed_consumers = _TOKEN_CONSUMER_MAP.get(token, set())
    if consumer_id and allowed_consumers and consumer_id not in allowed_consumers:
        raise HTTPException(status_code=403, ...)
    
    allowed_topics_from_map = _TOKEN_TOPIC_MAP.get(token, set())
    allowed_topics: set[str] | None
    if not allowed_topics_from_map:
        allowed_topics = None
    else:
        if topics:
            for topic in topics:
                if topic not in allowed_topics_from_map:
                    raise HTTPException(status_code=403, ...)
        allowed_topics = allowed_topics_from_map
    
    return {"topics": allowed_topics}
```

New code:
```python
async def require_consumer_identity(
    request: Request,
    consumer_id: str = "",
    topics: list[str] | None = None,
    principal: Principal = Depends(resolve_principal),
) -> dict[str, Any]:
    if consumer_id and principal.allowed_consumer_ids and consumer_id not in principal.allowed_consumer_ids:
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
    
    return {"topics": principal.allowed_topics}
```

Key changes:
- Uses `Depends(resolve_principal)` instead of `Depends(verify_bearer_token)`
- Uses `principal.allowed_consumer_ids` and `principal.allowed_topics` directly
- No longer queries `_TOKEN_CONSUMER_MAP` and `_TOKEN_TOPIC_MAP`
- Always raises HTTP 403 for insufficient permissions (never 401, since auth was already validated)

#### Step 7: Update middleware to delegate authentication (REQ-005, REQ-007)

Update `attach_auth_middleware()` (lines 232-284) to remove duplicate authentication while preserving `X-Request-Id` injection:

Current code:
```python
def attach_auth_middleware(app: Any) -> None:
    def _is_authorized(request: Request) -> bool:
        tok = getattr(request.app.state.config, "auth_token", "") or ""
        if not tok:
            return True
        header = request.headers.get("Authorization", "")
        if header == f"Bearer {tok}":
            return True
        if header.startswith("Bearer "):
            return header.removeprefix("Bearer ") in _TOKEN_ROLE_MAP
        return False
    
    async def _auth_middleware(request: Request, call_next):
        req_id = str(__import__("uuid").uuid4())
        request.state.request_id = req_id
        if not _is_authorized(request):
            return JSONResponse({"error": "Unauthorized"}, status_code=401)
        response = await call_next(request)
        response.headers["X-Request-Id"] = req_id
        return response
    
    app.add_middleware(BaseHTTPMiddleware, dispatch=_auth_middleware)
```

New code:
```python
def attach_auth_middleware(app: Any) -> None:
    """Register X-Request-Id middleware on a FastAPI app.
    
    Authentication is delegated to endpoint dependencies via resolve_principal().
    This middleware only injects X-Request-Id into responses.
    """
    from fastapi import Request  # noqa: F401
    from fastapi.responses import JSONResponse
    
    async def _request_id_middleware(request: Request, call_next):  # noqa: ANN001,ANN202
        """Inject X-Request-Id into response headers."""
        req_id = str(__import__("uuid").uuid4())
        request.state.request_id = req_id
        response = await call_next(request)
        response.headers["X-Request-Id"] = req_id
        return response
    
    app.add_middleware(BaseHTTPMiddleware, dispatch=_request_id_middleware)
```

Key changes:
- Removes `_is_authorized()` check — authentication delegated to endpoint dependencies
- Preserves `X-Request-Id` injection
- Simplifies middleware to single responsibility (request ID injection only)

### Details

- REQ-001: Principal dataclass introduced with roles, allowed_consumer_ids, allowed_topics, token_fingerprint.
- REQ-002: `resolve_principal()` replaces `verify_bearer_token()`, returning Principal.
- REQ-003: `require_role()` and `require_consumer_identity()` use Principal fields directly.
- REQ-004: HTTP 401 for unknown/missing tokens; HTTP 403 for insufficient roles. Raw tokens never logged.
- REQ-005: Endpoint dependencies become sole authentication authority.
- REQ-006: Per-role tokens mapped to principals via existing `_TOKEN_ROLE_MAP`.
- REQ-007: Middleware no longer performs duplicate authentication checks.
- REQ-009: String-prefix route authorization removed.
- REQ-010: FastAPI-native route metadata used (no custom route matching).

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.
- The `replay_ceil` variable scope and lifecycle remain unchanged.

## Security considerations

- Raw token values never logged — `token_fingerprint` used instead.
- All unauthorized responses use HTTP 401 or HTTP 403.
- `resolve_principal()` always raises HTTP 401 for unknown/missing tokens before any authorization check.

## Rollback considerations

- Revert requires restoring original `verify_bearer_token()`, `require_role()`, and `require_consumer_identity()` functions.
- The revert is mechanical — no semantic changes beyond restoring original function signatures.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/auth.py | Unit: Principal resolution contract | uv run pytest tests/eventbus/test_eventbus_auth.py -v | All new tests pass |
| scripts/eventbus/auth.py | Static analysis: no raw token exposure | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/auth.py | Type checking | uv run mypy scripts/eventbus/auth.py | No new type errors |
| scripts/eventbus/app.py | Integration: principal wired through endpoints | uv run pytest tests/eventbus/test_eventbus_auth.py -v | All endpoint tests pass |

## Completion criteria

- [ ] `Principal` dataclass introduced with all four fields (roles, allowed_consumer_ids, allowed_topics, token_fingerprint).
- [ ] `resolve_principal()` replaces `verify_bearer_token()`, returning Principal.
- [ ] `require_role()` uses `Depends(resolve_principal)` and compares against `principal.roles`.
- [ ] `require_consumer_identity()` uses `principal.allowed_consumer_ids` and `principal.allowed_topics` directly.
- [ ] Middleware delegates authentication to endpoint dependencies while preserving `X-Request-Id` injection.
- [ ] String-prefix route authorization removed from `require_role()`.
- [ ] All existing tests pass without modification.
- [ ] No new static analysis or type-checking errors are introduced.

## Out of scope

- Changes to the `/subscribe` endpoint's query parameters or HTTP response format.
- Changes to the `broker.py` subscriber lifecycle or disconnect mechanism.
- Changes to the `db.py` consumer offset storage logic.
- Changes to the `config.py` replay_batch_size parameter.
- Documentation updates (handled separately per REQ-008).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Introduce Principal dataclass | Pending | — | — | |
| 2 | Add token fingerprint derivation | Pending | — | — | |
| 3 | Replace verify_bearer_token with resolve_principal | Pending | — | — | |
| 4 | Replace require_role with principal-aware version | Pending | — | — | |
| 5 | Replace require_consumer_identity to use Principal | Pending | — | — | |
| 6 | Update middleware to delegate authentication | Pending | — | — | |
| 7 | Wire Principal through app.py | Pending | — | — | |
| 8 | Run validation suite | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004, REQ-005, REQ-006, REQ-007, REQ-009, REQ-010
- **Source issue**: issues/20260914-102249_eventbus02_principal-based-authentication-authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-171329_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-195002
- **Related target files**: scripts/eventbus/auth.py
