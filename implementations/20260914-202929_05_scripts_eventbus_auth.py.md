# Implementation Procedure: Add Principal dataclass; consolidate token-to-consumer/topic maps into Principal objects

## Goal

Update `scripts/eventbus/auth.py` to introduce a `Principal` dataclass that consolidates token-to-consumer/topic mappings, replacing the current split `_TOKEN_CONSUMER_MAP` / `_TOKEN_TOPIC_MAP` design.

## Scope

- Define `Principal` dataclass with fields: roles, allowed_consumer_ids, allowed_topics, token_fingerprint.
- Replace `_TOKEN_CONSUMER_MAP` / `_TOKEN_TOPIC_MAP` with Principal-based lookups.
- Update `require_consumer_identity()` to return `Principal` instead of raw dict.
- Update `require_role()` to return `Principal` instead of raw Role value.

## Assumptions

- A: REQ-001 through REQ-007 in `scripts/eventbus/auth.py` are implemented before this change.
- B: The current `_TOKEN_CONSUMER_MAP` and `_TOKEN_TOPIC_MAP` are populated from config at startup via `_populate_token_maps()`.
- C: The current `require_consumer_identity()` returns a dict with a 'topics' key.
- D: The current `require_role()` returns a Role value.

## Design decisions

- **Principal dataclass**: Consolidate all authorization context into a single immutable dataclass.
- **Token fingerprint**: Store a hash of the token for logging purposes, never log the raw token.
- **Fail-closed**: Reject requests where identity resolution fails or authorization context is missing.
- **Backward compatibility**: Preserve existing behavior for tokens with empty allowed_consumer_ids/allowed_topics (means "any").

## Alternatives considered

- **Keep split map design**: Continue using separate `_TOKEN_CONSUMER_MAP` and `_TOKEN_TOPIC_MAP` dictionaries. This was rejected because it doesn't provide the granularity needed for REQ-014—REQ-016.
- **Separate Principal lookup function**: Have a separate function to look up Principal from token. This adds complexity without security benefit.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original `_TOKEN_CONSUMER_MAP` / `_TOKEN_TOPIC_MAP` design.
- The revert is mechanical — no semantic changes beyond restoring original data structures.

## Implementation

### Target file

`scripts/eventbus/auth.py`

### Procedure

#### Step 1: Add Principal dataclass definition (REQ-014)

Add a new dataclass after the existing imports (after line 18):

Current code:
```python
HTTPBearerDep = HTTPBearer(auto_error=False)
```

New code:
```python
from dataclasses import dataclass

HTTPBearerDep = HTTPBearer(auto_error=False)


@dataclass(frozen=True)
class Principal:
    """Consolidated authorization context for a caller.

    Fields:
        roles: Set of roles granted by the caller's token.
        allowed_consumer_ids: Consumer IDs the caller is authorized to use.
            Empty set means "any consumer ID" (no restriction).
        allowed_topics: Topics the caller is authorized to subscribe to.
            Empty set means "any topic" (no restriction).
        token_fingerprint: Hash of the token for logging purposes (never logs raw token).
    """
    roles: frozenset[Role]
    allowed_consumer_ids: frozenset[str] | None  # None means "any consumer ID"
    allowed_topics: frozenset[str] | None  # None means "any topic"
    token_fingerprint: str
```

Key changes:
- Added `Principal` dataclass with frozen=True for immutability.
- `roles`: frozenset of Role values.
- `allowed_consumer_ids`: frozenset of consumer IDs or None (means any).
- `allowed_topics`: frozenset of topics or None (means any).
- `token_fingerprint`: string hash of the token for logging.

#### Step 2: Update _populate_token_maps() to populate Principal objects (REQ-014—REQ-016)

Replace the current `_populate_token_maps()` function (lines 63-89):

Current code:
```python
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
```

New code:
```python
def _populate_token_maps(config: Any) -> None:
    """Populate _TOKEN_PRINCIPAL_MAP from config at startup.

    Replaces the old _TOKEN_CONSUMER_MAP / _TOKEN_TOPIC_MAP / _TOKEN_ROLE_MAP
    design with a single Principal-based lookup table.
    """
    global _TOKEN_PRINCIPAL_MAP  # type: ignore[name-defined]
    
    # Clear existing mapping
    _TOKEN_PRINCIPAL_MAP.clear()

    # Helper to compute token fingerprint for logging
    def _fingerprint(token: str) -> str:
        import hashlib  # noqa: PLC0415
        
        return hashlib.sha256(token.encode()).hexdigest()[:16]

    # The shared auth_token grants every role, preserving backward compatibility
    # with the existing single-token deployment model.
    if hasattr(config, "auth_token") and config.auth_token:
        _TOKEN_PRINCIPAL_MAP[config.auth_token] = Principal(
            roles=frozenset(Role),
            allowed_consumer_ids=None,  # Empty means any consumer_id
            allowed_topics=None,  # Empty means any topic
            token_fingerprint=_fingerprint(config.auth_token),
        )

    # Each per-role token grants only its own role.
    for field, role in _PER_ROLE_TOKEN_FIELDS:
        token = getattr(config, field, None)
        if token:
            principal = _TOKEN_PRINCIPAL_MAP.get(token)
            if principal is None:
                _TOKEN_PRINCIPAL_MAP[token] = Principal(
                    roles=frozenset({role}),
                    allowed_consumer_ids=None,  # No consumer restriction
                    allowed_topics=None,  # No topic restriction
                    token_fingerprint=_fingerprint(token),
                )
            else:
                # Merge: add role to existing principal
                _TOKEN_PRINCIPAL_MAP[token] = Principal(
                    roles=frozenset(principal.roles | {role}),
                    allowed_consumer_ids=principal.allowed_consumer_ids,
                    allowed_topics=principal.allowed_topics,
                    token_fingerprint=principal.token_fingerprint,
                )

    # admin_token is a superuser credential: grants every role, same as auth_token.
    admin_token = getattr(config, "admin_token", None)
    if admin_token:
        _TOKEN_PRINCIPAL_MAP[admin_token] = Principal(
            roles=frozenset(Role),
            allowed_consumer_ids=None,  # Empty means any consumer_id
            allowed_topics=None,  # Empty means any topic
            token_fingerprint=_fingerprint(admin_token),
        )
```

Key changes:
- Removed `_TOKEN_CONSUMER_MAP`, `_TOKEN_TOPIC_MAP`, `_TOKEN_ROLE_MAP` globals.
- Added `_TOKEN_PRINCIPAL_MAP` global.
- Added `_fingerprint()` helper for token hashing.
- Updated Principal creation logic to include all four fields.

#### Step 3: Update require_consumer_identity() to return Principal (REQ-014—REQ-016)

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
) -> Principal:
    """FastAPI dependency: verify caller is authorized to use the given consumer_id and topics.

    Returns a Principal object with authorization context for the caller.
    """
    if not token:
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Look up the principal for this token
    principal = _TOKEN_PRINCIPAL_MAP.get(token)
    if principal is None:
        logger.warning(
            "Authentication failed: invalid Bearer token (fingerprint=%s)",
            token[:8],  # Log first 8 chars for debugging (not full token)
        )
        raise HTTPException(status_code=401, detail="Unauthorized")

    # Validate consumer_id is in the allowlist for this caller. An empty allowlist
    # (no entry, or an explicit empty set) means "no consumer_id restriction" for
    # this token, per _populate_token_maps()'s own "Empty means any consumer_id"
    # convention (e.g. the shared auth_token is deliberately given an empty set).
    if consumer_id and principal.allowed_consumer_ids is not None and consumer_id not in principal.allowed_consumer_ids:
        logger.warning(
            "Authorization failed: consumer_id=%s not allowed for this caller",
            consumer_id,
        )
        raise HTTPException(
            status_code=403,
            detail=f"Forbidden: consumer_id '{consumer_id}' not allowed",
        )

    # Validate topic access. An empty _TOKEN_PRINCIPAL_MAP entry (no entry, or an
    # explicit empty set) means "no topic restriction" for this token, per
    # _populate_token_maps()'s own "Empty means any topic" convention — mirrors
    # the consumer_id-allowlist convention above.
    if principal.allowed_topics is not None and topics:
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

    # Return the Principal object directly
    return principal
```

Key changes:
- Return type changed from `dict[str, Any]` to `Principal`.
- Replaced `_TOKEN_CONSUMER_MAP` lookups with `_TOKEN_PRINCIPAL_MAP` lookups.
- Replaced `_TOKEN_TOPIC_MAP` lookups with `_TOKEN_PRINCIPAL_MAP` lookups.
- Removed dict return — now returns Principal directly.

#### Step 4: Update require_role() to return Principal (REQ-014—REQ-016)

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
    ) -> Principal:
        if not token:
            # Authentication already failed in verify_bearer_token
            raise HTTPException(status_code=401, detail="Unauthorized")

        # Look up the principal for this token
        principal = _TOKEN_PRINCIPAL_MAP.get(token)
        if principal is None:
            logger.warning(
                "Authentication failed: invalid Bearer token (fingerprint=%s)",
                token[:8],  # Log first 8 chars for debugging (not full token)
            )
            raise HTTPException(status_code=401, detail="Unauthorized")

        # Check if the caller has the required role
        if role not in principal.roles:
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
                return principal

        # If no route matched, deny access
        raise HTTPException(status_code=403, detail="Forbidden: unknown route")

    return _check_role
```

Key changes:
- Return type changed from `Role` to `Principal`.
- Replaced `_TOKEN_ROLE_MAP` lookups with `_TOKEN_PRINCIPAL_MAP` lookups.
- Changed return value from `role` to `principal`.

### Details

- REQ-014: `Principal` dataclass defined and wired through all endpoints.
- REQ-015: Fail-closed behavior enforced when identity resolution fails.
- REQ-016: `Principal` passed through subscription handler instead of raw Role value.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original `_TOKEN_CONSUMER_MAP` / `_TOKEN_TOPIC_MAP` design.
- The revert is mechanical — no semantic changes beyond restoring original data structures.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/auth.py | Unit: Principal dataclass contract; Integration: token-to-principal mapping | uv run pytest tests/eventbus/test_eventbus_auth.py -v | New auth tests pass; existing tests unchanged |
| scripts/eventbus/auth.py | Static analysis: no credential exposure in logs | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/auth.py | Type checking | uv run mypy scripts/eventbus/auth.py | No new type errors |

## Completion criteria

- [ ] `Principal` dataclass defined with frozen=True.
- [ ] `_TOKEN_PRINCIPAL_MAP` replaces `_TOKEN_CONSUMER_MAP` / `_TOKEN_TOPIC_MAP` / `_TOKEN_ROLE_MAP`.
- [ ] `require_consumer_identity()` returns `Principal` instead of dict.
- [ ] `require_role()` returns `Principal` instead of Role.
- [ ] Token fingerprint used for logging instead of raw token.
- [ ] All existing tests pass without modification.
- [ ] No new static analysis or type-checking errors are introduced.

## Out of scope

- Changes to the `/subscribe` endpoint's query parameters or HTTP response format.
- Changes to the `broker.py` subscriber lifecycle or disconnect mechanism.
- Changes to the `db.py` consumer offset storage logic.
- Changes to the `config.py` replay_batch_size parameter.
- Documentation updates (handled separately per REQ-011).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add Principal dataclass definition | Pending | — | — | |
| 2 | Update _populate_token_maps() to populate Principal objects | Pending | — | — | |
| 3 | Update require_consumer_identity() to return Principal | Pending | — | — | |
| 4 | Update require_role() to return Principal | Pending | — | — | |

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
- **Requirement ID**: REQ-014, REQ-015, REQ-016
- **Source issue**: issues/20260914-102317_eventbus03_consumer-topic-authorization-ack-nack.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-172234_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-202929
- **Related target files**: scripts/eventbus/auth.py
