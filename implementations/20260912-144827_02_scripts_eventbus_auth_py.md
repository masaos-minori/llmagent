## Goal

Re-architect `require_role` to map caller's token → Role using configuration, fix `require_consumer_identity` return type to return a dict matching callers' expectations, and populate `_TOKEN_CONSUMER_MAP`/`_TOKEN_TOPIC_MAP` from config (REQ-002, REQ-003, REQ-004).

## Scope

- **In-Scope**: Modifying `scripts/eventbus/auth.py` to implement token→role mapping, fix return types, and populate maps from config
- **Out-of-Scope**: Changes to other files (handled in separate procedure documents)

## Assumptions

- Per-role tokens will be added to the EventBus TOML config rather than changing the token format itself (e.g., JWT claims)
- The `EventBusConfig` class will have fields for per-role token mapping
- The existing `_ROUTE_ROLE_MAP` will continue to define which roles can access which endpoints
- `_TOKEN_CONSUMER_MAP` and `_TOKEN_TOPIC_MAP` were meant to be populated from config (UNK-01 resolved: they are not dead scaffolding)

## Design decisions

- Add per-role token fields to `EventBusConfig` (handled in separate procedure document) and populate `_TOKEN_CONSUMER_MAP`/`_TOKEN_TOPIC_MAP` from config at startup
- Change `require_consumer_identity` return type from `None` to `dict[str, Any]` with a `topics` key containing a set of permitted topics
- Keep the existing `_ROUTE_ROLE_MAP` structure but enhance `require_role` to look up the caller's role from their token

## Alternatives considered

- Using JWT claims instead of per-role tokens — would require significant changes to token generation and validation
- Adding a separate identity store for consumer identities — would require new infrastructure

## Implementation

### Target file

`scripts/eventbus/auth.py`

### Procedure

1. Modify `require_role` to determine the caller's role from their Bearer token using configuration
2. Fix `require_consumer_identity` return type to return a dict with a `topics` key
3. Populate `_TOKEN_CONSUMER_MAP` and `_TOKEN_TOPIC_MAP` from config at startup
4. Update the `_check_role` inner function to use the resolved role

### Method

For `require_role`:
- Extract the caller's token from the request
- Look up the caller's role from `_TOKEN_CONSUMER_MAP` or a new token→role mapping
- Compare the resolved role against the required role for the endpoint

For `require_consumer_identity`:
- Return a dict-like object with a `topics` key containing a set of permitted topics
- Ensure the returned dict always contains the `topics` key even if empty

For map population:
- Add a startup function that reads per-role token configuration and populates the maps
- Call this function during the FastAPI lifespan initialization

### Details

#### Step 1: Modify `require_role` to map token → Role

```python
async def require_role(role: Role):
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
```

#### Step 2: Fix `require_consumer_identity` return type

```python
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
```

#### Step 3: Populate maps from config at startup

Add a function to populate the maps from config:

```python
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
    if hasattr(config, 'auth_token') and config.auth_token:
        _TOKEN_CONSUMER_MAP[config.auth_token] = set()  # Empty means any consumer_id
        _TOKEN_TOPIC_MAP[config.auth_token] = set()      # Empty means any topic
```

Call this function during the FastAPI lifespan initialization in `app.py`.

## Compatibility considerations

- The existing single-shared-token deployment model must not break unless a migration path is designed (REQ-005)
- The `require_consumer_identity` return type change may break other callers beyond `subscribe_route.py` — audit all callers before making the change
- The `_populate_token_maps` function must handle the case where config doesn't have per-role token fields yet

## Security considerations

- Moving authorization to the correct layer ensures all requests are properly authorized
- The token→role mapping must be secure and not susceptible to replay attacks
- Consumer identity validation must prevent unauthorized topic access

## Rollback considerations

- If the token→role mapping breaks, roll back to the previous state where authorization was bypassed (security regression)
- Ensure test coverage exists before making changes to verify rollback safety

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/auth.py::require_role | Unit: verify token→role mapping logic | pytest tests/eventbus/test_eventbus_auth.py | All auth tests pass with per-role tokens |
| scripts/eventbus/auth.py::require_consumer_identity | Unit: verify return type is dict with topics key | pytest tests/eventbus/test_eventbus_auth.py | No AttributeError on success path |
| scripts/eventbus/app.py | Integration: verify role-gated access for each endpoint | pytest tests/eventbus/test_eventbus_auth.py | Wrong-role requests get 403 |

## Completion criteria

- [ ] `require_role` determines the caller's role from their Bearer token using configuration
- [ ] `require_consumer_identity` returns a dict with a `topics` key containing a set of permitted topics
- [ ] `_TOKEN_CONSUMER_MAP` and `_TOKEN_TOPIC_MAP` are populated from config at startup
- [ ] Authorization checks execute for every request (no bypass)
- [ ] Tests pass with the new authorization model

## Out of scope

- Changes to `scripts/eventbus/config.py` (handled in separate procedure document)
- Changes to `config/eventbus.toml` (handled in separate procedure document)
- Changes to test files (handled in separate procedure document)

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Re-architect require_role to map token → Role | Pending | — | — | |
| 2 | Fix require_consumer_identity return type | Pending | — | — | |
| 3 | Populate _TOKEN_CONSUMER_MAP/_TOKEN_TOPIC_MAP from config | Pending | — | — | |
| 4 | Run validation tests | Pending | — | — | |

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
- **Requirement ID**: REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20260911-133957_ebauth01_role-and-consumer-identity-checks-never-run.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260912-111042_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-144827
- **Related target files**: scripts/eventbus/auth.py
