# Implementation Procedure: Verify EventBus Auth Module Structure (Read-Only Reference)

## Goal

Document the current state of `scripts/eventbus/auth.py` as evidence for EVENTBUS-008 reconciliation and ADR-013 stale claim correction. This is a read-only verification step — no modifications to this file are required.

## Scope

- Read-only inspection of `scripts/eventbus/auth.py`
- Confirm Role enum, _ROUTE_ROLE_MAP, and token maps exist
- Verify auth middleware attachment mechanism

## Assumptions

- Current implementation reflects intended design
- Auth middleware provides sufficient protection for the EventBus HTTP API

## Design decisions

- No changes to this file — documentation only
- Evidence gathered here supports ADR-013 Problem section correction and EVENTBUS-008 resolution confirmation

## Alternatives considered

### Alternative A: Modify auth.py to add additional auth layers

**Reason for rejection:** The existing auth middleware + route-level role checks provide adequate protection. Additional layers would be scope creep beyond reconciliation.

## Implementation

### Target file

`scripts/eventbus/auth.py` (read-only)

### Procedure

1. Verify Role enum definition (lines 21-25)
2. Verify _ROUTE_ROLE_MAP definition (lines 29-39)
3. Verify token map definitions (lines 43-52)
4. Verify _populate_token_maps function (lines 63-88)
5. Verify verify_bearer_token function (lines 103-125)
6. Verify require_role function (lines 128-172)
7. Verify require_consumer_identity function (lines 175-229)
8. Verify attach_auth_middleware function (lines 232-284)
9. Run auth-related tests

### Method

Read-only inspection and test execution.

### Details

#### Step 1: Verify Role enum

Lines 21-25 confirm four roles:
```python
class Role(StrEnum):
    PUBLISHER = "publisher"
    CONSUMER = "consumer"
    OPERATOR = "operator"
    MONITORING = "monitoring"
```

#### Step 2: Verify _ROUTE_ROLE_MAP

Lines 29-39 define route-to-role mapping:
```python
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
}
```

#### Step 3: Verify token maps

Lines 43-52 define token-to-consumer/topic/role mappings:
```python
_TOKEN_CONSUMER_MAP: dict[str, set[str]] = {}
_TOKEN_TOPIC_MAP: dict[str, set[str]] = {}
_TOKEN_ROLE_MAP: dict[str, set[Role]] = {}
```

#### Step 4: Verify _populate_token_maps

Lines 63-88 populate token maps from config at startup:
- Shared auth_token grants every role (backward compatibility)
- Per-role tokens grant only their own role
- admin_token grants every role (superuser)

#### Step 5: Verify verify_bearer_token

Lines 103-125 verify Bearer token and return token value or raise 401.

#### Step 6: Verify require_role

Lines 128-172 implement FastAPI dependency factory for role-based authorization:
- Determines caller's role from Bearer token
- Checks if that role is allowed for the requested endpoint
- Returns 403 if unauthorized

#### Step 7: Verify require_consumer_identity

Lines 175-229 implement FastAPI dependency for consumer identity validation:
- Validates consumer_id is in allowlist for the caller
- Validates topic access for the caller
- Returns dict with 'topics' key

#### Step 8: Verify attach_auth_middleware

Lines 232-284 register Bearer-token auth middleware on FastAPI app:
- Must be called exactly once, immediately after FastAPI app construction
- Reads auth_token from request.app.state.config on each request
- Returns 401 for unauthorized requests
- Injects X-Request-Id response header

#### Step 9: Run auth-related tests

Run:
```bash
pytest tests/eventbus/ -k auth
```

Expected: All auth-related tests pass.

## Compatibility considerations

- Existing consumers of EventBus rely on the current auth mechanism
- Adding additional auth layers would change the public contract
- The existing auth approach is compatible with the current architecture

## Security considerations

- The auth middleware + route-level role checks provide defense-in-depth
- Consumer identity validation adds an additional layer for consumer-facing routes
- Token maps are populated from config at startup, not dynamically
- Empty token maps mean "no restriction" (any consumer_id/topic allowed)

## Rollback considerations

- No code changes — no rollback needed
- If auth is later found insufficient, revert the Status field in ADR-013 Problem section to "open"

## Validation plan

1. Confirm auth.py still defines Role enum with four roles
2. Confirm _ROUTE_ROLE_MAP covers all routes
3. Confirm token maps are populated from config
4. Confirm verify_bearer_token validates tokens correctly
5. Confirm require_role checks role authorization
6. Confirm require_consumer_identity validates consumer identity
7. Confirm attach_auth_middleware registers middleware correctly
8. Run auth-related tests

## Completion criteria

- [ ] Role enum confirmed with four roles
- [ ] _ROUTE_ROLE_MAP covers all routes
- [ ] Token maps defined and populated from config
- [ ] verify_bearer_token validates tokens correctly
- [ ] require_role checks role authorization
- [ ] require_consumer_identity validates consumer identity
- [ ] attach_auth_middleware registers middleware correctly
- [ ] Auth tests pass

## Out of scope

- Modifying auth.py to add additional auth layers
- Changing the auth middleware implementation
- Adding new authentication mechanisms
- Updating other files

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify Role enum | Pending | — | — | |
| 2 | Verify _ROUTE_ROLE_MAP | Pending | — | — | |
| 3 | Verify token maps | Pending | — | — | |
| 4 | Verify _populate_token_maps | Pending | — | — | |
| 5 | Verify verify_bearer_token | Pending | — | — | |
| 6 | Verify require_role | Pending | — | — | |
| 7 | Verify require_consumer_identity | Pending | — | — | |
| 8 | Verify attach_auth_middleware | Pending | — | — | |
| 9 | Run auth tests | Pending | — | — | |

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
- **Requirement ID**: REQ-004 (auth middleware integration)
- **Source issue**: N/A
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-180730_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260915-000842
- **Related target files**: scripts/eventbus/auth.py
