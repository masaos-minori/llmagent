# Implementation Procedure: Move failure-state inspection under shared lock; update caller to use new return signature

## Goal

Update `scripts/eventbus/dlq_route.py` to move failure-state inspection under shared lock and update the caller to use the new return signature from `redeliver_event()`.

## Scope

- Move failure-state inspection under shared lock in `dlq_requeue()`.
- Update `dlq_requeue()` caller to use new return signature `(success, new_event_id, new_seq)`.
- Eliminate the separate seq lookup outside the lock.

## Assumptions

- A: The `redelivered_from` existence check in `redeliver_event()` provides a concurrency guard against duplicate redeliveries — confirmed by `db.py:516-521`.
- B: `run_with_db_lock()` acquires and releases a shared SQLite lock around the callback — confirmed by `route_helpers.py` usage pattern.
- C: The current `dlq_requeue()` function fetches `new_seq` outside the lock (lines 78-83) — confirmed by `dlq_route.py:78-83`.
- D: The `redeliver_event()` function returns `(success, new_event_id)` but NOT `new_seq` — confirmed by `db.py:510-512`.
- E: `EVENTBUS-002` concerns `/replay?format=json` pagination format documentation — confirmed by `docs/00_governance_03_issue-and-uncertainty-management.md:185-202`.
- F: The `docs/eventbus/` directory does not exist yet — confirmed by filesystem check.

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

`scripts/eventbus/dlq_route.py`

### Procedure

#### Step 1: Move failure-state inspection under shared lock and update caller to use new return signature (REQ-001, REQ-002)

Replace the current `dlq_requeue()` function (lines 50-91):

Current code:
```python
async def dlq_requeue(
    request: Request,
    event_id: str,
    _role: Role | None = None,  # set by app.py wrapper
) -> dict[str, Any]:
    """Requeue a dead-letter queue entry back into the active event queue.

    Uses the lineage model: each requeue creates a new event row with
    redelivered_from pointing to the original event_id. The original row's
    dlq_at is intentionally left set so only one redeliver succeeds per
    original event.
    """
    db = get_db(request)

    def _redeliver() -> tuple[bool, str | None]:
        """Redeliver a single event from the dead letter queue using the lineage model."""
        success, new_event_id = redeliver_event(db, event_id)
        return (success, new_event_id)

    success, new_event_id = await run_with_db_lock(_redeliver)
    if success:
        logger.info("dlq redelivered event_id=%s -> %s", event_id, new_event_id)
        resp: dict[str, Any] = {
            "event_id": event_id,
            "requeued": True,
            "new_event_id": new_event_id,
        }
        # Include new_seq by fetching the seq of the newly inserted row
        row = db.execute(
            "SELECT seq FROM events WHERE event_id = ?",
            (new_event_id,),
        ).fetchone()
        if row is not None:
            resp["new_seq"] = int(row[0])
        return resp
    # Event exists but is not currently in DLQ — dlq_at IS NULL means event was already redelivered or acked
    row = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?", (event_id,)
    ).fetchone()
    if row is not None:
        raise HTTPException(status_code=409, detail=ERR_EVENT_NOT_IN_DLQ)
    raise HTTPException(status_code=404, detail=ERR_EVENT_NOT_FOUND)
```

New code:
```python
async def dlq_requeue(
    request: Request,
    event_id: str,
    _role: Role | None = None,  # set by app.py wrapper
) -> dict[str, Any]:
    """Requeue a dead-letter queue entry back into the active event queue.

    Uses the lineage model: each requeue creates a new event row with
    redelivered_from pointing to the original event_id. The original row's
    dlq_at is intentionally left set so only one redeliver succeeds per
    original event.
    """
    db = get_db(request)

    def _redeliver_and_inspect():
        """Redeliver a single event from the dead letter queue using the lineage model, with failure-state inspection under lock."""
        success, new_event_id, new_seq = redeliver_event(db, event_id)
        if not success:
            # Inspect failure state under lock
            row = db.execute(
                "SELECT dlq_at FROM events WHERE event_id = ?", (event_id,)
            ).fetchone()
            if row is not None:
                return (False, ERR_EVENT_NOT_IN_DLQ, 409)
            return (False, ERR_EVENT_NOT_FOUND, 404)
        return (True, new_event_id, new_seq)

    result = await run_with_db_lock(_redeliver_and_inspect)
    if isinstance(result, tuple) and len(result) == 3:
        _, detail, status_code = result
        raise HTTPException(status_code=status_code, detail=detail)
    
    success, new_event_id, new_seq = result
    if success:
        logger.info("dlq redelivered event_id=%s -> %s", event_id, new_event_id)
        resp: dict[str, Any] = {
            "event_id": event_id,
            "requeued": True,
            "new_event_id": new_event_id,
            "new_seq": new_seq,
        }
        return resp
    # Event exists but is not currently in DLQ — dlq_at IS NULL means event was already redelivered or acked
    row = db.execute(
        "SELECT dlq_at FROM events WHERE event_id = ?", (event_id,)
    ).fetchone()
    if row is not None:
        raise HTTPException(status_code=409, detail=ERR_EVENT_NOT_IN_DLQ)
    raise HTTPException(status_code=404, detail=ERR_EVENT_NOT_FOUND)
```

Key changes:
- Extended `_redeliver()` to `_redeliver_and_inspect()` with failure-state inspection under lock.
- Updated caller to use new return signature `(success, new_event_id, new_seq)`.
- Eliminated the separate seq lookup outside the lock.
- Added `new_seq` to the response dictionary.

### Details

- REQ-001: Redelivery, new-sequence lookup, and failure-state inspection moved under shared database lock.
- REQ-002: One transaction returning inserted sequence atomically.

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
| scripts/eventbus/dlq_route.py | Integration: concurrent requeue behavior | uv run pytest tests/eventbus/test_eventbus_dlq.py -v | Concurrent requeue tests pass |
| scripts/eventbus/dlq_route.py | Static analysis: no credential exposure in logs | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/dlq_route.py | Type checking | uv run mypy scripts/eventbus/dlq_route.py | No new type errors |

## Completion criteria

- [ ] Failure-state inspection moved under shared lock.
- [ ] Caller updated to use new return signature.
- [ ] Separate seq lookup eliminated.
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
| 1 | Move failure-state inspection under shared lock | Pending | — | — | |
| 2 | Update caller to use new return signature | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002
- **Source issue**: issues/20260914-102435_eventbus06_dlq-promotion-requeue-atomicity.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-173831_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-230211
- **Related target files**: scripts/eventbus/dlq_route.py
