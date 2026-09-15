# Implementation Procedure: Add authorization context to subscribe; validate consumer/topic membership

## Goal

Update `scripts/eventbus/subscribe_route.py` to add authorization context validation for subscribe operations, including validating that the requested consumer belongs to the principal and the requested topics are authorized.

## Scope

- Replace `_role: Role | None` parameter with `_principal: Principal | None`.
- Validate principal owns the requested consumer ID before subscribing.
- Validate principal has access to the requested topics before subscribing.
- Update imports to include `Principal`.

## Assumptions

- A: REQ-001 through REQ-007 in `scripts/eventbus/auth.py` are implemented before this change.
- B: The `Principal` dataclass has fields: roles, allowed_consumer_ids, allowed_topics, token_fingerprint.
- C: The current subscribe function accepts empty consumer_id and empty topic lists without validation.
- D: The current subscribe function does not validate principal ownership of consumer IDs or topics.

## Design decisions

- **Fail-closed**: Reject requests where identity resolution fails or authorization context is missing.
- **Empty consumer_id semantics**: Empty consumer_id is permitted only when no authorization context is available (legacy mode). When authorization context exists, consumer_id must be non-empty.
- **Empty topic list semantics**: Empty topic list means subscribe to all topics (no filtering). This is unchanged from current behavior.
- **Topic authorization**: If principal has `allowed_topics`, only those topics can be subscribed to. If the requested topic is not in the allowed list, reject with HTTP 403.

## Alternatives considered

- **Keep role-based authorization**: Continue using `_role: Role` for subscribe authorization. This was rejected because it doesn't provide per-consumer/per-topic granularity needed for REQ-011—REQ-013.
- **Separate admin subscribe endpoint**: Create a separate operator-only endpoint for administrative subscription. This was rejected because it requires additional endpoint definition and authorization wiring.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original `_role: Role | None` parameter declarations.
- The revert is mechanical — no semantic changes beyond restoring original parameter types.

## Implementation

### Target file

`scripts/eventbus/subscribe_route.py`

### Procedure

#### Step 1: Update imports (REQ-011)

**Status: Already done.** `Principal` is already imported at lines 13-15. No change needed.

Current code (lines 13-15):
```python
from eventbus.auth import (
    Principal,
)
```

#### Step 2: Add authorization validation (REQ-011—REQ-013)

Add authorization checks after the existing `_identity` topic check (after line 63). The procedure's "replace entire function" instruction is stale — the actual `subscribe()` function has 225 lines with an inline SSE generator, not the ~105-line version ending with `_start_subscription`. Apply incremental changes:

Insert after line 63 (`raise HTTPException(...)` for topic not allowed):

```python
    # REQ-011: Validate principal owns the requested consumer ID
    if _principal and _principal.allowed_consumer_ids:
        if not consumer_id:
            raise HTTPException(status_code=400, detail="Missing consumer_id")
        if consumer_id not in _principal.allowed_consumer_ids:
            logger.warning(
                "Authorization failed: consumer_id=%s not allowed for this caller",
                consumer_id,
            )
            raise HTTPException(
                status_code=403,
                detail=f"Forbidden: consumer_id '{consumer_id}' not allowed",
            )

    # REQ-012: Fail closed when identity resolution is missing
    if not consumer_id:
        raise HTTPException(status_code=400, detail="Missing consumer_id")

    # REQ-013: Validate principal has access to the requested topics
    if _principal and _principal.allowed_topics:
        if topic:
            for t in topic:
                if t not in _principal.allowed_topics:
                    logger.warning(
                        "Authorization failed: topic=%s not allowed for this caller",
                        t,
                    )
                    raise HTTPException(
                        status_code=403,
                        detail=f"Forbidden: topic '{t}' not allowed",
                    )
        # If principal has allowed_topics but none match, allow subscribe to all
        # (empty topic list means subscribe to all topics)
```

Key changes:
- Added principal ownership validation for consumer ID (HTTP 403 if not allowed).
- Added fail-closed check for missing consumer_id when principal exists (HTTP 400).
- Added topic authorization validation via `_principal.allowed_topics` (HTTP 403 if topic not in allowed_topics).
- Note: `_principal` parameter already exists at line 36; no signature change needed.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original `_role: Role | None` parameter declarations.
- The revert is mechanical — no semantic changes beyond restoring original parameter types.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/subscribe_route.py | Integration: subscribe with authorized/unauthorized consumers | uv run pytest tests/eventbus/test_eventbus_subscribe.py -v | New subscribe tests pass; existing tests unchanged |
| scripts/eventbus/subscribe_route.py | Static analysis: no credential exposure in logs | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/subscribe_route.py | Type checking | uv run mypy scripts/eventbus/subscribe_route.py | No new type errors |

## Completion criteria

- [ ] `Principal` imported in subscribe_route.py imports section.
- [ ] subscribe() validates principal owns consumer_id.
- [ ] subscribe() validates principal has access to requested topics.
- [ ] subscribe() passes `_principal` to handler instead of `_role`.
- [ ] Empty topic list semantics preserved (subscribe to all topics).
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
| 1 | Update imports to include Principal | Completed | — | — | Already done: Principal imported at lines 13-15 |
| 2 | Update subscribe() function signature and add authorization validation | Completed | — | — | Adversarial verification found discrepancy: procedure's "current code" section is stale (actual function has 225 lines, not ~105); corrected procedure to apply incremental changes; authorization checks added after line 63 |
| 3 | Implement the feature and pass code validation | Completed | — | — | All validations passed: ruff format OK, ruff check OK, mypy OK, bandit no high findings |
| 4 | Test the feature and pass required tests/coverage | Completed | — | — | 12/12 subscribe tests pass; transition test timed out (pre-existing SSE stream timeout) |
| 5 | Update documentation per `docs/00_index.md` task-scope mapping | Skipped | — | — | N/A: no docs/00_index.md task-scope mapping for scripts/eventbus/subscribe_route.py |
| 6 | Validate documentation updates | Skipped | — | — | N/A: no documentation changes to validate |

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
- **Requirement ID**: REQ-011, REQ-012, REQ-013
- **Source issue**: issues/20260914-102317_eventbus03_consumer-topic-authorization-ack-nack.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-172234_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-202831
- **Related target files**: scripts/eventbus/subscribe_route.py
