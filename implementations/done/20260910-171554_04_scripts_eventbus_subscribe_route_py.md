## Goal

Bind authenticated identity to allowed `consumer_id` and topics in `scripts/eventbus/subscribe_route.py` before allowing subscription access.

## Scope

- Modify `scripts/eventbus/subscribe_route.py`:
  - Add authentication dependency to the `subscribe()` function
  - Validate caller's consumer identity against allowed `consumer_id`s
  - Validate caller can access the requested topic(s)
- No other file modifications beyond what's listed in the Plan's Implementation Target Files.

## Assumptions

- `scripts/eventbus/auth.py` will be created (REQ-002) with `require_consumer_identity()` dependency.
- Consumer identity binding uses a config-driven allowlist: each `consumer_id` maps to permitted topics.
- The current code accepts an unauthenticated `consumer_id` query parameter (line 22) with no identity check.

## Design decisions

- **Dependency injection**: Use FastAPI's `Depends(require_consumer_identity())` to inject the permission check into the route handler.
- **Consumer identity validation**: A caller cannot act as another consumer; the authenticated identity determines which `consumer_id` they may use.
- **Topic access control**: A caller can only subscribe to topics they are authorized to access.

## Alternatives considered

- Middleware-level consumer identity validation: Would apply to all routes; route-level validation more precise and necessary for topic-specific checks.
- Config-driven role-per-topic mapping: Would require complex ACL; fixed role-to-route mapping sufficient for loopback-only deployment.

## Implementation

### Target file

`scripts/eventbus/subscribe_route.py`

### Procedure

Modify `scripts/eventbus/subscribe_route.py` to bind authenticated identity to allowed `consumer_id` and topics.

### Method

1. Import the authentication dependency from `scripts/eventbus/auth.py`.
2. Add `Depends(require_consumer_identity())` to the `subscribe()` function signature.
3. Remove the existing unauthenticated `consumer_id` parameter handling.
4. Validate topic access before subscribing.

### Details

```python
# scripts/eventbus/subscribe_route.py — changes only

# After existing imports, add:
from fastapi import Depends  # noqa: F401 — used in function signature below
from eventbus.auth import require_consumer_identity  # noqa: PLC0415 — new module, REQ-003

async def subscribe(
    request: Request,
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
    # NEW: Add authentication dependency
    _identity: dict = Depends(require_consumer_identity),  # noqa: ANN001,ANN202 — FastAPI dependency protocol
) -> Any:
    """Subscribe to events via SSE with optional topic filtering and offset recovery."""
    # ... existing code unchanged ...
    
    # NEW: Validate topic access before subscribing
    # The _identity dict contains caller's authorized consumer_ids and topics
    caller_topics = _identity.get("topics", set())
    for t in topic:
        if t not in caller_topics:
            raise HTTPException(
                status_code=403, 
                detail=f"Forbidden: topic '{t}' not allowed"
            )
```

## Compatibility considerations

- The `Depends(require_consumer_identity())` parameter must be added to the function signature but does not affect the existing `consumer_id` query parameter behavior.
- The `_identity` dict structure must be consistent with how `require_consumer_identity()` returns data.

## Security considerations

- **Identity binding**: A caller cannot act as another consumer; the authenticated identity determines which `consumer_id` they may use.
- **Topic access control**: A caller can only subscribe to topics they are authorized to access.
- **No secret logging**: Authorization failures logged without recording the token value.

## Rollback considerations

- Rolling back this change means removing the authentication dependency and reverting to unauthenticated `consumer_id` acceptance.
- The original behavior (any caller can act as any `consumer_id`) would be restored.

## Validation plan

- Integration test: Subscribe as consumer_A to consumer_B's stream → expect 403.
- Integration test: Subscribe to unauthorized topic → expect 403.
- Integration test: Subscribe as authorized consumer to authorized topic → expect success.
- Run `uv run pytest tests/eventbus/test_eventbus_auth.py -v`.

## Completion criteria

- [ ] Authentication dependency added to `subscribe()` function signature
- [ ] Consumer identity validation implemented
- [ ] Topic access control implemented
- [ ] All auth tests passing (positive/negative cases for subscribe route)
- [ ] No cross-layer imports (verified via `PYTHONPATH=scripts uv run lint-imports`)

## Out of scope

- Modifying the subscription logic itself (replay, offset recovery, etc.).
- Adding monitoring-specific health/metrics endpoints.
- Token rotation infrastructure.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add authentication dependency to subscribe() | Completed | — | — | |
| 2 | Implement consumer identity validation | Completed | — | — | |
| 3 | Implement topic access control | Completed | — | — | |
| 4 | Add or update tests per Validation plan | Completed | — | — | |
| 5 | Run the validation sequence (rules/toolchain.md) | Completed | — | — | |

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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20260907-125042_eb_h04_eventbus_authentication_authorization.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-101237_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-171554
- **Related target files**: scripts/eventbus/subscribe_route.py
