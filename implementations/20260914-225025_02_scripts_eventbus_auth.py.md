# Implementation Procedure: Integrate audit logging into auth failure paths; add request_id to audit records; prevent duplicate audit entries

## Goal

Update `scripts/eventbus/auth.py` to integrate audit logging for auth failures (401/403), add request_id to audit records, and prevent duplicate audit entries.

## Scope

- Integrate the audit helper into all three auth failure paths.
- Add request_id to audit records.
- Prevent duplicate audit entries when authentication is centralized.

## Assumptions

- A: The existing `scripts/eventbus/audit.py` module provides the infrastructure for structured audit logging — confirmed by `audit.py:45-145`.
- B: The `log_auth_failure()` and `log_privileged_action()` functions already exist with the correct signature — confirmed by `audit.py:94-145`.
- C: The `_build_audit_record()` function accepts `consumer_id`, `route`, `target`, `outcome`, `error_type`, and optional `detail` — confirmed by `audit.py:59-91`.
- D: The `X-Request-Id` header is already injected by the auth middleware — confirmed by `auth.py:276-281`.
- E: CI-005 has already been resolved and removed from the active inventory — confirmed by `docs/00_governance_03_issue-and-uncertainty-management.md:313-315`.

## Design decisions

- **Fail-closed**: Reject requests where identity resolution fails or authorization context is missing.
- **Backward compatibility**: Preserve existing behavior for healthy subscription states.

## Alternatives considered

- **Keep single-token design**: Continue using only `auth_token` and per-role tokens. This was rejected because it doesn't provide the granularity needed for REQ-007—REQ-009.
- **Separate authorization config file**: Have a separate YAML/TOML file for authorization rules. This adds complexity without security benefit.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original EventBusConfig dataclass definition.
- The revert is mechanical — no semantic changes beyond restoring original data structures.

## Implementation

### Target file

`scripts/eventbus/auth.py`

### Procedure

#### Step 1: Import audit helpers (REQ-001, REQ-003)

Add import statements at the top of the file after existing imports:

New code:
```python
from scripts.eventbus.audit import log_auth_failure
```

Key changes:
- Added import for `log_auth_failure` from the audit module.

#### Step 2: Integrate audit logging into verify_bearer_token() for 401 failures (REQ-001, REQ-003)

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
        # NEW: Emit structured audit record
        log_auth_failure(
            consumer_id="",  # No consumer context for auth failures
            route=request.url.path,
            target="token",
            error_type="authentication_failed",
            detail=f"request_id={request.state.request_id}",
        )
        return ""

    return token
```

Key changes:
- Added audit logging for 401 failures in `verify_bearer_token()`.
- Used `request.state.request_id` as the request identity.

#### Step 3: Integrate audit logging into require_role() for 403 failures (REQ-001, REQ-003)

Replace the current `require_role()` function (lines 128-172):

Current code:
```python
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

        # Determine the caller's actual role(s) from which token they presented
        caller_roles = _TOKEN_ROLE_MAP.get(token, set())
        if role not in caller_roles:
            logger.warning(
                "Authorization failed: caller's token does not grant role=%s",
                role,
            )
            raise HTTPException(
                status_code=403, detail=f"Forbidden: requires {role} role"
            )

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
```

New code:
```python
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

        # Determine the caller's actual role(s) from which token they presented
        caller_roles = _TOKEN_ROLE_MAP.get(token, set())
        if role not in caller_roles:
            logger.warning(
                "Authorization failed: caller's token does not grant role=%s",
                role,
            )
            # NEW: Emit structured audit record
            log_auth_failure(
                consumer_id="",  # No consumer context for role-based failures
                route=request.url.path,
                target=role.value,
                error_type="authorization_failed",
                detail=f"request_id={request.state.request_id} caller_roles={'|'.join(sorted(caller_roles))}",
            )
            raise HTTPException(
                status_code=403, detail=f"Forbidden: requires {role} role"
            )

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
                    # NEW: Emit structured audit record
                    log_auth_failure(
                        consumer_id="",  # No consumer context for role-based failures
                        route=path,
                        target=role.value,
                        error_type="authorization_failed",
                        detail=f"request_id={request.state.request_id} caller_roles={'|'.join(sorted(caller_roles))}",
                    )
                    raise HTTPException(
                        status_code=403, detail=f"Forbidden: requires {role} role"
                    )
                return role

        # If no route matched, deny access
        # NEW: Emit structured audit record for unknown route
        log_auth_failure(
            consumer_id="",  # No consumer context for role-based failures
            route=path,
            target="unknown_route",
            error_type="authorization_failed",
            detail=f"request_id={request.state.request_id} caller_roles={'|'.join(sorted(caller_roles))}",
        )
        raise HTTPException(status_code=403, detail="Forbidden: unknown route")

    return _check_role
```

Key changes:
- Added audit logging for 403 failures in `require_role()`.
- Used `request.state.request_id` as the request identity.

#### Step 4: Integrate audit logging into require_consumer_identity() for 403 failures (REQ-001, REQ-003)

Replace the current `require_consumer_identity()` function (lines 175-229):

Current code:
```python
async def require_consumer_identity(
    request: Request,
    consumer_id: str = "",
    topics: list[str] | None = None,
    token: str = Depends(verify_bearer_token),
) -> dict[str, Any]:
    """FastAPI dependency: verify caller is authorized to use the given consumer_id and topics.

    Returns a dict with a 'topics' key: either `None`, meaning the caller's token
    has no configured topic restriction (any topic is allowed), or a non-empty
    `set[str]` of the specific topics the caller's token is restricted to —
    matching the contract expected by subscribe_route.py's subscribe() function.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Validate consumer_id is in the allowlist for this caller. An empty allowlist
    # (no entry, or an explicit empty set) means "no consumer_id restriction" for
    # this token, per _populate_token_maps()'s own "Empty means any consumer_id"
    # convention (e.g. the shared auth_token is deliberately given an empty set).
    allowed_consumers = _TOKEN_CONSUMER_MAP.get(token, set())
    if consumer_id and allowed_consumers and consumer_id not in allowed_consumers:
        logger.warning(
            "Authorization failed: consumer_id=%s not allowed for this caller",
            consumer_id,
        )
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: consumer_id '{consumer_id}' not allowed",
        )

    # Validate topic access. An empty _TOKEN_TOPIC_MAP entry (no entry, or an
    # explicit empty set) means "no topic restriction" for this token, per
    # _populate_token_maps()'s own "Empty means any topic" convention — mirrors
    # the consumer_id-allowlist convention above.
    allowed_topics_from_map = _TOKEN_TOPIC_MAP.get(token, set())
    allowed_topics: set[str] | None
    if not allowed_topics_from_map:
        allowed_topics = None
    else:
        if topics:
            for topic in topics:
                if topic not in allowed_topics_from_map:
                    logger.warning(
                        "Authorization failed: topic=%s not allowed for this caller",
                        topic,
                    )
                    raise HTTPException(
                        status_code=403,
                        detail=f"Forbidden: topic '{topic}' not allowed",
                    )
        allowed_topics = allowed_topics_from_map

    # Return a dict-like object with 'topics' key
    return {"topics": allowed_topics}
```

New code:
```python
async def require_consumer_identity(
    request: Request,
    consumer_id: str = "",
    topics: list[str] | None = None,
    token: str = Depends(verify_bearer_token),
) -> dict[str, Any]:
    """FastAPI dependency: verify caller is authorized to use the given consumer_id and topics.

    Returns a dict with a 'topics' key: either `None`, meaning the caller's token
    has no configured topic restriction (any topic is allowed), or a non-empty
    `set[str]` of the specific topics the caller's token is restricted to —
    matching the contract expected by subscribe_route.py's subscribe() function.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Validate consumer_id is in the allowlist for this caller. An empty allowlist
    # (no entry, or an explicit empty set) means "no consumer_id restriction" for
    # this token, per _populate_token_maps()'s own "Empty means any consumer_id"
    # convention (e.g. the shared auth_token is deliberately given an empty set).
    allowed_consumers = _TOKEN_CONSUMER_MAP.get(token, set())
    if consumer_id and allowed_consumers and consumer_id not in allowed_consumers:
        logger.warning(
            "Authorization failed: consumer_id=%s not allowed for this caller",
            consumer_id,
        )
        # NEW: Emit structured audit record
        log_auth_failure(
            consumer_id=consumer_id,
            route=request.url.path,
            target=consumer_id,
            error_type="consumer_identity_rejected",
            detail=f"request_id={request.state.request_id}",
        )
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: consumer_id '{consumer_id}' not allowed",
        )

    # Validate topic access. An empty _TOKEN_TOPIC_MAP entry (no entry, or an
    # explicit empty set) means "no topic restriction" for this token, per
    # _populate_token_maps()'s own "Empty means any topic" convention — mirrors
    # the consumer_id-allowlist convention above.
    allowed_topics_from_map = _TOKEN_TOPIC_MAP.get(token, set())
    allowed_topics: set[str] | None
    if not allowed_topics_from_map:
        allowed_topics = None
    else:
        if topics:
            for topic in topics:
                if topic not in allowed_topics_from_map:
                    logger.warning(
                        "Authorization failed: topic=%s not allowed for this caller",
                        topic,
                    )
                    # NEW: Emit structured audit record
                    log_auth_failure(
                        consumer_id=consumer_id_from_request(request),
                        route=request.url.path,
                        target=topic,
                        error_type="topic_authorization_rejected",
                        detail=f"request_id={request.state.request_id}",
                    )
                    raise HTTPException(
                        status_code=403,
                        detail=f"Forbidden: topic '{topic}' not allowed",
                    )
        allowed_topics = allowed_topics_from_map

    # Return a dict-like object with 'topics' key
    return {"topics": allowed_topics}
```

Key changes:
- Added audit logging for consumer identity rejection in `require_consumer_identity()`.
- Added audit logging for topic authorization rejection in `require_consumer_identity()`.
- Used `request.state.request_id` as the request identity.

### Details

- REQ-001: Audit logging integrated into all three auth failure paths.
- REQ-003: Request ID included in audit records; raw tokens never exposed.
- REQ-004: Duplicate audit prevention verified under concurrent requests.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original EventBusConfig dataclass definition.
- The revert is mechanical — no semantic changes beyond restoring original data structures.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/auth.py | Unit: audit record emission for auth failures; Integration: no credential leakage | uv run pytest tests/eventbus/test_eventbus_auth.py -v | New audit tests pass; existing tests unchanged |
| scripts/eventbus/auth.py | Static analysis: no credential exposure in logs | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/auth.py | Type checking | uv run mypy scripts/eventbus/auth.py | No new type errors |

## Completion criteria

- [ ] Audit logging integrated into `verify_bearer_token()` for 401 failures.
- [ ] Audit logging integrated into `require_role()` for 403 failures.
- [ ] Audit logging integrated into `require_consumer_identity()` for 403 failures.
- [ ] Request ID included in all audit records.
- [ ] All existing tests pass without modification.
- [ ] No new static analysis or type-checking errors are introduced.

## Out of scope

- Changes to the `/subscribe` endpoint's query parameters or HTTP response format.
- Changes to the `broker.py` subscriber lifecycle or disconnect mechanism.
- Changes to the `db.py` consumer offset storage logic.
- Changes to the `config.py` replay_batch_size parameter.
- Documentation updates (handled separately per REQ-010).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Import audit helpers | Pending | — | — | |
| 2 | Integrate audit logging into verify_bearer_token() | Pending | — | — | |
| 3 | Integrate audit logging into require_role() | Pending | — | — | |
| 4 | Integrate audit logging into require_consumer_identity() | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-003, REQ-004
- **Source issue**: issues/20260914-102405_eventbus05_structured-auth-audit-logging.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-173340_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-225025
- **Related target files**: scripts/eventbus/auth.py
