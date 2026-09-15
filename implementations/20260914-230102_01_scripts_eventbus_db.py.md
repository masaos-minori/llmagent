# Implementation Procedure: Extend redeliver_event() signature to return (success, new_event_id, new_seq); compute new_seq atomically within same transaction

## Goal

Update `scripts/eventbus/db.py` to extend the `redeliver_event()` signature to return `(success, new_event_id, new_seq)` where `new_seq` is computed atomically within the same transaction using `lastrowid`.

## Scope

- Extend `redeliver_event()` return signature to include `new_seq`.
- Compute `new_seq` atomically within the same transaction using `lastrowid`.
- Eliminate the need for a separate seq lookup outside the lock.

## Assumptions

- A: The `redelivered_from` existence check in `redeliver_event()` provides a concurrency guard against duplicate redeliveries — confirmed by `db.py:516-521`.
- B: `run_with_db_lock()` acquires and releases a shared SQLite lock around the callback — confirmed by `route_helpers.py` usage pattern.
- C: The current `dlq_requeue()` function fetches `new_seq` outside the lock (lines 78-83) — confirmed by `dlq_route.py:78-83`.
- D: The `redeliver_event()` function returns `(success, new_event_id)` but NOT `new_seq` — confirmed by `db.py:510-512`.
- E: `EVENTBUS-002` concerns `/replay?format=json` pagination format documentation — confirmed by `docs/00_governance_03_issue-and-uncertainty-management.md:185-202`.
- F: The `docs/eventbus/` directory does not exist yet — confirmed by filesystem check.

## Design decisions

- **Additive change**: Only add `new_seq` field to the return tuple; do not remove or modify existing fields.
- **Atomic computation**: Use `lastrowid` to compute `new_seq` atomically at insert time.
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

- Revert requires restoring original redeliver_event() return signature.
- The revert is mechanical — no semantic changes beyond restoring original data structures.

## Implementation

### Target file

`scripts/eventbus/db.py`

### Procedure

#### Step 1: Extend redeliver_event() signature to return (success, new_event_id, new_seq) (REQ-001, REQ-002)

Replace the current `redeliver_event()` function (lines 495-538):

Current code:
```python
def redeliver_event(
    conn: sqlite3.Connection, event_id: str, now: str | None = None
) -> tuple[bool, str | None]:
    """Redeliver a dead-lettered event by inserting a new row with lineage.

    Uses a `redelivered_from`-existence check as a concurrency guard: if another
    request has already redelivered this event (i.e., a row exists with
    redelivered_from = event_id), return (False, None) to prevent duplicate
    redeliveries. This prevents the race condition where two concurrent requests
    could both see dlq_at IS NOT NULL and both insert new rows.

    Performs conditional-update guard on the original row (WHERE event_id = ? AND dlq_at IS NOT NULL)
    then inserts a new row with a fresh UUID v4 event_id, copied delivery_failure_count,
    cycle_failure_count=0, and redelivered_from set to the original event_id.

    Returns (success, new_event_id):
      - (True, new_event_id)   = event found and redelivered
      - (False, None)          = event not found in DLQ or already redelivered
    """
    # Concurrency guard: check if this event has already been redelivered
    # by looking for an existing row with redelivered_from = event_id
    existing_redelivery = conn.execute(
        "SELECT 1 FROM events WHERE redelivered_from = ?",
        (event_id,),
    ).fetchone()
    if existing_redelivery:
        return (False, None)

    ts = now if now is not None else "strftime('%Y-%m-%dT%H:%M:%SZ', 'now')"
    new_event_id = uuid.uuid4().hex
    cur = conn.execute(
        f"UPDATE events SET {_COL_DLQ_REQUEUE_COUNT} = {_COL_DLQ_REQUEUE_COUNT} + 1 WHERE {_COL_EVENT_ID} = ? AND {_COL_DLQ_AT} IS NOT NULL",  # nosec B608 — column names are module-level constants, values parameterized
        (event_id,),
    )
    if cur.rowcount == 0:
        return (False, None)
    conn.execute(
        f"INSERT INTO events ({_COL_EVENT_ID}, topic, payload, producer, published_at, {_COL_DELIVERY_FAILURE_COUNT}, {_COL_CYCLE_FAILURE_COUNT}, redelivered_from) "
        f"SELECT ?, topic, payload, producer, {ts}, {_COL_DELIVERY_FAILURE_COUNT}, 0, ? "
        f"FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608 — column names are module-level constants, values parameterized
        (new_event_id, event_id, event_id),
    )
    conn.commit()
    return (True, new_event_id)
```

New code:
```python
def redeliver_event(
    conn: sqlite3.Connection, event_id: str, now: str | None = None
) -> tuple[bool, str | None, int | None]:
    """Redeliver a dead-lettered event by inserting a new row with lineage.

    Uses a `redelivered_from`-existence check as a concurrency guard: if another
    request has already redelivered this event (i.e., a row exists with
    redelivered_from = event_id), return (False, None, None) to prevent duplicate
    redeliveries. This prevents the race condition where two concurrent requests
    could both see dlq_at IS NOT NULL and both insert new rows.

    Performs conditional-update guard on the original row (WHERE event_id = ? AND dlq_at IS NOT NULL)
    then inserts a new row with a fresh UUID v4 event_id, copied delivery_failure_count,
    cycle_failure_count=0, and redelivered_from set to the original event_id.

    Returns (success, new_event_id, new_seq):
      - (True, new_event_id, new_seq)   = event found and redelivered
      - (False, None, None)             = event not found in DLQ or already redelivered
    """
    # Concurrency guard: check if this event has already been redelivered
    # by looking for an existing row with redelivered_from = event_id
    existing_redelivery = conn.execute(
        "SELECT 1 FROM events WHERE redelivered_from = ?",
        (event_id,),
    ).fetchone()
    if existing_redelivery:
        return (False, None, None)

    ts = now if now is not None else "strftime('%Y-%m-%dT%H:%M:%SZ', 'now')"
    new_event_id = uuid.uuid4().hex
    cur = conn.execute(
        f"UPDATE events SET {_COL_DLQ_REQUEUE_COUNT} = {_COL_DLQ_REQUEUE_COUNT} + 1 WHERE {_COL_EVENT_ID} = ? AND {_COL_DLQ_AT} IS NOT NULL",  # nosec B608 — column names are module-level constants, values parameterized
        (event_id,),
    )
    if cur.rowcount == 0:
        return (False, None, None)
    insert_cur = conn.execute(
        f"INSERT INTO events ({_COL_EVENT_ID}, topic, payload, producer, published_at, {_COL_DELIVERY_FAILURE_COUNT}, {_COL_CYCLE_FAILURE_COUNT}, redelivered_from) "
        f"SELECT ?, topic, payload, producer, {ts}, {_COL_DELIVERY_FAILURE_COUNT}, 0, ? "
        f"FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608 — column names are module-level constants, values parameterized
        (new_event_id, event_id, event_id),
    )
    # NEW: Compute new_seq atomically within the same transaction using lastrowid
    new_seq = int(insert_cur.lastrowid) if insert_cur.lastrowid else None
    conn.commit()
    return (True, new_event_id, new_seq)
```

Key changes:
- Extended return signature from `tuple[bool, str | None]` to `tuple[bool, str | None, int | None]`.
- Added `new_seq` computation using `insert_cur.lastrowid` after INSERT.
- Updated docstring to reflect new return value.

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

- Revert requires restoring original redeliver_event() return signature.
- The revert is mechanical — no semantic changes beyond restoring original data structures.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/db.py | Unit: atomic redelivery+seq return | uv run pytest tests/eventbus/test_eventbus_dlq.py -v | New DB tests pass; existing tests unchanged |
| scripts/eventbus/db.py | Static analysis: no credential exposure in logs | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/db.py | Type checking | uv run mypy scripts/eventbus/db.py | No new type errors |

## Completion criteria

- [ ] `redeliver_event()` return signature extended to include `new_seq`.
- [ ] `new_seq` computed atomically within same transaction using `lastrowid`.
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
| 1 | Extend redeliver_event() signature to return (success, new_event_id, new_seq) | Completed | 20260915-135023 | 20260915-135023 |  |
| 2 | Compute new_seq atomically within same transaction using lastrowid | Completed | 20260915-135032 | 20260915-135032 |  |

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
- **Generated at**: 20260914-230102
- **Related target files**: scripts/eventbus/db.py