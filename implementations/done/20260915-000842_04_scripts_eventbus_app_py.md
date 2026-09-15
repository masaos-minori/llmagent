# Implementation Procedure: Verify EventBus Auth Middleware Attachment (Read-Only Reference)

## Goal

Document the current state of `scripts/eventbus/app.py` as evidence for EVENTBUS-008 reconciliation and ADR-013 stale claim correction. This is a read-only verification step — no modifications to this file are required.

## Scope

- Read-only inspection of `scripts/eventbus/app.py`
- Confirm auth middleware attachment
- Verify route-level authentication requirements

## Assumptions

- Current implementation reflects intended design
- Auth middleware provides sufficient protection for the EventBus HTTP API

## Design decisions

- No changes to this file — documentation only
- Evidence gathered here supports ADR-013 Problem section correction and EVENTBUS-008 resolution confirmation

## Alternatives considered

### Alternative A: Modify app.py to add additional auth layers

**Reason for rejection:** The existing auth middleware + route-level role checks provide adequate protection. Additional layers would be scope creep beyond reconciliation.

## Implementation

### Target file

`scripts/eventbus/app.py` (read-only)

### Procedure

1. Verify attach_auth_middleware(app) call (line 144)
2. Verify auth imports (lines 19-25)
3. Verify each route requires role-based authentication
4. Verify consumer identity validation on ACK/NACK/subscribe endpoints
5. Run test suite to confirm auth behavior

### Method

Read-only inspection and test execution.

### Details

#### Step 1: Verify auth middleware attachment

Line 144 confirms:
```python
attach_auth_middleware(app)
```

This is called immediately after FastAPI app creation, ensuring all routes go through the auth middleware.

#### Step 2: Verify auth imports

Lines 19-25 show auth module imports:
```python
from eventbus.auth import (
    Role,
    _populate_token_maps,  # noqa: PLC0415 — new module, REQ-004
    attach_auth_middleware,  # noqa: PLC0415 — new module, REQ-002
    require_consumer_identity,
    require_role,
)
```

Key observations:
- Role enum imported for type hints
- attach_auth_middleware imported for middleware setup
- require_role imported for route-level role checks
- require_consumer_identity imported for consumer-specific validation
- _populate_token_maps imported for token map initialization

#### Step 3: Verify route-level authentication

Each route uses Depends(require_role(...)) for role-based access:

| Route | Required Role | Consumer Identity Check |
|-------|--------------|------------------------|
| /health | None (public) | No |
| /publish | PUBLISHER | No |
| /replay | OPERATOR | No |
| /subscribe | CONSUMER | Yes |
| /dlq | OPERATOR | No |
| /dlq/{id}/requeue | OPERATOR | No |
| /events/{id}/ack | CONSUMER | Yes |
| /nack | CONSUMER | Yes |

#### Step 4: Verify consumer identity validation

Consumer-facing routes (/subscribe, /ack, /nack) additionally use Depends(require_consumer_identity):
```python
_identity: dict[str, Any] = Depends(require_consumer_identity)
```

This validates the caller's bearer token and, when configured, a consumer_id allowlist.

#### Step 5: Verify token map population

Lifespan function (line 69) populates token maps from config:
```python
_populate_token_maps(app.state.config)
```

#### Step 6: Run test suite

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
- Loopback-only binding check (config.py line 66-70) provides network-level protection
- Token maps are populated from config at startup, not dynamically

## Rollback considerations

- No code changes — no rollback needed
- If auth is later found insufficient, revert the Status field in ADR-013 Problem section to "open"

## Validation plan

1. Confirm app.py still calls attach_auth_middleware(app)
2. Confirm each route requires appropriate role-based authentication
3. Confirm consumer identity validation exists on consumer-facing routes
4. Confirm token maps are populated from config
5. Run auth-related tests

## Completion criteria

- [ ] attach_auth_middleware(app) confirmed present
- [ ] Auth imports verified
- [ ] Each route's role requirement documented
- [ ] Consumer identity validation confirmed on consumer-facing routes
- [ ] Token map population confirmed
- [ ] Auth tests pass

## Out of scope

- Modifying app.py to add additional auth layers
- Changing the auth middleware implementation
- Adding new authentication mechanisms
- Updating other files

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Verify auth middleware attachment | Pending | — | — | |
| 2 | Verify auth imports | Pending | — | — | |
| 3 | Verify route-level authentication | Pending | — | — | |
| 4 | Verify consumer identity validation | Pending | — | — | |
| 5 | Verify token map population | Pending | — | — | |
| 6 | Run auth tests | Pending | — | — | |

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
- **Related target files**: scripts/eventbus/app.py
