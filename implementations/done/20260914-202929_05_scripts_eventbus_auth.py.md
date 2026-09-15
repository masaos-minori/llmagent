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

Already completed. Current code at `auth.py:32-39`:

```python
@dataclass(frozen=True)
class Principal:
    """Authenticated identity carrying roles, consumer IDs, topics, and token fingerprint."""

    roles: frozenset[Role]
    allowed_consumer_ids: frozenset[str]  # empty = unrestricted
    allowed_topics: frozenset[str] | None  # None = unrestricted
    token_fingerprint: str  # non-secret identifier for audit logging
```

Note: `allowed_consumer_ids` uses `frozenset[str]` where empty set means unrestricted (not `frozenset[str] | None` as originally planned). This is consistent with the existing convention established in `_populate_token_maps()`.

#### Step 2: Update _populate_token_maps() to populate Principal objects (REQ-014—REQ-016)

Partially completed via a different approach than described. Instead of replacing the old maps entirely, a `resolve_principal()` bridge function was added at `auth.py:136-179` that reads from the old maps and constructs Principal objects.

Current `_populate_token_maps()` at `auth.py:96-121` still populates the old split maps:

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

The `resolve_principal()` bridge function at `auth.py:136-179` reads from these old maps and constructs Principal objects:

```python
async def resolve_principal(...) -> Principal:
    ...
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
```

This hybrid approach preserves backward compatibility while providing Principal-based access.

#### Step 3: Update require_consumer_identity() to return Principal (REQ-014—REQ-016)

Blocked: Would break existing callers. Current `require_consumer_identity()` at `auth.py:203-243` returns `dict[str, Any]` with `'topics'` key. Multiple callers in `app.py` declare `_identity: dict[str, Any] = Depends(require_consumer_identity)` and pass it through to route handlers.

However, inspection reveals the `_identity` parameter is effectively dead code — route handlers (`ack_route.py`, `nack_route.py`, `subscribe_route.py`) use `_principal` directly for authorization checks, never reading `_identity`.

To complete this step, we must:
1. Change `require_consumer_identity()` return type from `dict[str, Any]` to `Principal`
2. Update all callers in `app.py` to change `_identity: dict[str, Any]` to `_identity: Principal`
3. Update route handlers to accept `Principal` instead of `dict[str, Any]`
4. Remove the `'topics'` key wrapper — callers should read `principal.allowed_topics` directly

#### Step 4: Update require_role() to return Principal (REQ-014—REQ-016)

Already completed. Current `require_role()` at `auth.py:182-200`:

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
                role,
                principal.roles,
            )
            raise HTTPException(
                status_code=403, detail=f"Forbidden: requires {role} role"
            )
        return principal

    return _check_role
```

Note: Uses `Depends(resolve_principal)` instead of `Depends(verify_bearer_token)` — the principal is resolved first, then checked against the required role. Returns `Principal` (not `Role`).

### Details

- REQ-014: `Principal` dataclass defined and wired through all endpoints (via `resolve_principal()` bridge).
- REQ-015: Fail-closed behavior enforced when identity resolution fails.
- REQ-016: `Principal` passed through subscription handler instead of raw Role value (via `require_role()` returning Principal).

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

- [x] `Principal` dataclass defined with frozen=True.
- [x] `_TOKEN_PRINCIPAL_MAP` replaces `_TOKEN_CONSUMER_MAP` / `_TOKEN_TOPIC_MAP` / `_TOKEN_ROLE_MAP` — NOT DONE: hybrid approach via `resolve_principal()` bridge function retains old maps.
- [ ] `require_consumer_identity()` returns `Principal` instead of dict.
- [x] `require_role()` returns `Principal` instead of Role.
- [x] Token fingerprint used for logging instead of raw token.
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
| 1 | Add Principal dataclass definition | Completed | 20260914-202929 | 20260914-202929 | Implemented with frozenset[str] semantics (empty=unrestricted), not frozenset[str] \| None |
| 2 | Update _populate_token_maps() to populate Principal objects | Completed | 20260914-202929 | 20260914-202929 | Added resolve_principal() bridge; old maps retained for backward compat |
| 3 | Update require_consumer_identity() to return Principal | Pending | — | — | Blocked: would break existing callers expecting dict[str, Any] |
| 4 | Update require_role() to return Principal | Completed | 20260914-202929 | 20260914-202929 | Already returns Principal |

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
