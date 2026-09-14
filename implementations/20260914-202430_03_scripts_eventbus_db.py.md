# Implementation Procedure: Add delivery-state verification for ACK; add consumer failure/retry semantics for NACK

## Goal

Update `scripts/eventbus/db.py` to add delivery-state verification for ACK operations and add consumer-specific failure/retry semantics for NACK operations.

## Scope

- Add delivery-state verification to `ack_event_for_consumer()` to ensure event was delivered to the consumer.
- Add consumer-specific failure counter to `nack_event()` for per-consumer retry decisions.
- Define consumer failure/retry counter semantics separate from global event-level counter.

## Assumptions

- A: REQ-001 through REQ-007 in `scripts/eventbus/auth.py` are implemented before this change.
- B: The `Principal` dataclass has fields: roles, allowed_consumer_ids, allowed_topics, token_fingerprint.
- C: The current `nack_event()` uses a single global `delivery_failure_count` counter.
- D: The current `ack_event_for_consumer()` tracks per-consumer delivery state but does not verify prior delivery before accepting ACK.

## Design decisions

- **Consumer-specific failure counters**: Track consumer failures separately from global event-level failures. Two counters:
  - `delivery_failure_count` (global, event-level): used for DLQ promotion threshold
  - `consumer_delivery_failure_count` (per-consumer): used for consumer-specific retry decisions
- **Delivery-state verification**: Before accepting ACK/NACK, verify the event was actually delivered to the requesting consumer.
- **Fail-closed**: Reject requests where identity resolution fails or authorization context is missing.

## Alternatives considered

- **Keep single-counter approach**: Use only the global `delivery_failure_count` for both DLQ promotion and consumer-specific retry decisions. This was rejected because it doesn't distinguish between consumer-specific failures and global failures.
- **Separate DLQ promotion logic**: Have DLQ promotion check only the global counter while consumer-specific retry checks the consumer counter. This adds complexity without security benefit.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original `nack_event()` single-counter logic.
- The revert is mechanical — no semantic changes beyond restoring original function signatures.

## Implementation

### Target file

`scripts/eventbus/db.py`

### Procedure

#### Step 1: Add consumer failure counter column constant (REQ-010)

Add a new constant after the existing column constants (after line 37):

Current code:
```python
_COL_REDISTRIBUTED_FROM = "redelivered_from"
```

New code:
```python
_COL_REDISTRIBUTED_FROM = "redelivered_from"
_COL_CONSUMER_DELIVERY_FAILURE_COUNT = "consumer_delivery_failure_count"
```

#### Step 2: Update _migrate() to add consumer failure counter column (REQ-010)

Replace the current migration logic for adding columns (lines 101-143):

Current code:
```python
def _migrate(conn: sqlite3.Connection) -> None:
    """Add new columns and indexes if they don't already exist; drop removed columns."""
    for col in (_COL_DELIVERY_FAILURE_COUNT, _COL_DLQ_REQUEUE_COUNT):
        try:
            conn.execute(
                f"ALTER TABLE events ADD COLUMN {col} INTEGER NOT NULL DEFAULT 0"
            )
            logger.info("migrated: added column %s to events", col)
        except sqlite3.OperationalError as exc:
            if exc.args and "duplicate column name" in exc.args[0]:
                pass  # column already exists
            else:
                raise

    for col in (_COL_CYCLE_FAILURE_COUNT, _COL_REDISTRIBUTED_FROM):
        try:
            if col == "cycle_failure_count":
                conn.execute(
                    f"ALTER TABLE events ADD COLUMN {col} INTEGER NOT NULL DEFAULT 0"
                )
            else:
                conn.execute(f"ALTER TABLE events ADD COLUMN {col} TEXT")
            logger.info("migrated: added column %s to events", col)
        except sqlite3.OperationalError as exc:
            if exc.args and "duplicate column name" in exc.args[0]:
                pass  # column already exists
            else:
                raise

    try:
        conn.execute("ALTER TABLE events DROP COLUMN retry_count")
        logger.info("migrated: dropped column retry_count from events")
    except sqlite3.OperationalError as exc:
        if exc.args and "no such column" in exc.args[0].lower():
            pass  # already dropped, or table created fresh without it
        else:
            raise
```

New code:
```python
def _migrate(conn: sqlite3.Connection) -> None:
    """Add new columns and indexes if they don't already exist; drop removed columns."""
    for col in (_COL_DELIVERY_FAILURE_COUNT, _COL_DLQ_REQUEUE_COUNT):
        try:
            conn.execute(
                f"ALTER TABLE events ADD COLUMN {col} INTEGER NOT NULL DEFAULT 0"
            )
            logger.info("migrated: added column %s to events", col)
        except sqlite3.OperationalError as exc:
            if exc.args and "duplicate column name" in exc.args[0]:
                pass  # column already exists
            else:
                raise

    for col in (_COL_CYCLE_FAILURE_COUNT, _COL_REDISTRIBUTED_FROM):
        try:
            if col == "cycle_failure_count":
                conn.execute(
                    f"ALTER TABLE events ADD COLUMN {col} INTEGER NOT NULL DEFAULT 0"
                )
            else:
                conn.execute(f"ALTER TABLE events ADD COLUMN {col} TEXT")
            logger.info("migrated: added column %s to events", col)
        except sqlite3.OperationalError as exc:
            if exc.args and "duplicate column name" in exc.args[0]:
                pass  # column already exists
            else:
                raise

    # Add consumer-specific failure counter column
    try:
        conn.execute(
            f"ALTER TABLE events ADD COLUMN {_COL_CONSUMER_DELIVERY_FAILURE_COUNT} INTEGER NOT NULL DEFAULT 0"
        )
        logger.info("migrated: added column %s to events", _COL_CONSUMER_DELIVERY_FAILURE_COUNT)
    except sqlite3.OperationalError as exc:
        if exc.args and "duplicate column name" in exc.args[0]:
            pass  # column already exists
        else:
            raise

    try:
        conn.execute("ALTER TABLE events DROP COLUMN retry_count")
        logger.info("migrated: dropped column retry_count from events")
    except sqlite3.OperationalError as exc:
        if exc.args and "no such column" in exc.args[0].lower():
            pass  # already dropped, or table created fresh without it
        else:
            raise
```

Key changes:
- Added `_COL_CONSUMER_DELIVERY_FAILURE_COUNT` constant.
- Added migration logic to add `consumer_delivery_failure_count` column to events table.

#### Step 3: Update nack_event() to track consumer-specific failures (REQ-010)

Replace the current `nack_event()` function (lines 214-251):

Current code:
```python
def nack_event(conn: sqlite3.Connection, event_id: str) -> tuple[int, int]:
    """Increment delivery_failure_count and cycle_failure_count for an event.

    Only increments if the event is in Normal/Delivered state (acked_at IS NULL
    AND dlq_at IS NULL). Events that are already ACKed or DLQ'd cannot have their
    failure counts incremented — attempting to do so would corrupt state.

    Returns (delivery_failure_count, cycle_failure_count) on success, or:
      - (-1, -1) if the event was not found
      - (-2, -2) if the event is in an invalid state for NACK (already ACKed or DLQ'd)
    """
    try:
        cur = conn.execute(
            f"UPDATE events SET {_COL_DELIVERY_FAILURE_COUNT} = {_COL_DELIVERY_FAILURE_COUNT} + 1, {_COL_CYCLE_FAILURE_COUNT} = {_COL_CYCLE_FAILURE_COUNT} + 1 WHERE {_COL_EVENT_ID} = ? AND {_COL_ACKED_AT} IS NULL AND {_COL_DLQ_AT} IS NULL",  # nosec B608 — column names are module-level constants, values parameterized
            (event_id,),
        )
        conn.commit()
        if cur.rowcount == 0:
            existing = conn.execute(
                f"SELECT {_COL_ACKED_AT}, {_COL_DLQ_AT} FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608 — column names are module-level constants, values parameterized
                (event_id,),
            ).fetchone()
            if existing:
                return (-2, -2)
            return (-1, -1)
        row = conn.execute(
            f"SELECT {_COL_DELIVERY_FAILURE_COUNT}, {_COL_CYCLE_FAILURE_COUNT} FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608 — column names are module-level constants, values parameterized
            (event_id,),
        ).fetchone()
        if row:
            return (
                int(row[_COL_DELIVERY_FAILURE_COUNT]),
                int(row[_COL_CYCLE_FAILURE_COUNT]),
            )
        return (-1, -1)
    except Exception:
        conn.rollback()
        raise
```

New code:
```python
def nack_event(
    conn: sqlite3.Connection,
    event_id: str,
    consumer_id: str | None = None,  # Optional — for consumer-specific failure tracking
) -> tuple[int, int]:
    """Increment delivery_failure_count and cycle_failure_count for an event.

    Only increments if the event is in Normal/Delivered state (acked_at IS NULL
    AND dlq_at IS NULL). Events that are already ACKed or DLQ'd cannot have their
    failure counts incremented — attempting to do so would corrupt state.

    If consumer_id is provided, also increment the consumer-specific failure count.

    Returns (delivery_failure_count, cycle_failure_count) on success, or:
      - (-1, -1) if the event was not found
      - (-2, -2) if the event is in an invalid state for NACK (already ACKed or DLQ'd)
    """
    try:
        # Build the UPDATE statement with optional consumer-specific failure tracking
        update_clause = (
            f"{_COL_DELIVERY_FAILURE_COUNT} = {_COL_DELIVERY_FAILURE_COUNT} + 1, "
            f"{_COL_CYCLE_FAILURE_COUNT} = {_COL_CYCLE_FAILURE_COUNT} + 1"
        )
        where_clause = f"{_COL_EVENT_ID} = ? AND {_COL_ACKED_AT} IS NULL AND {_COL_DLQ_AT} IS NULL"
        params: list[str] = [event_id]
        
        if consumer_id is not None:
            # Also increment consumer-specific failure count
            update_clause += f", {_COL_CONSUMER_DELIVERY_FAILURE_COUNT} = {_COL_CONSUMER_DELIVERY_FAILURE_COUNT} + 1"
            where_clause += f" AND {_COL_CONSUMER_ID} = ?"
            params.append(consumer_id)
        
        sql = f"UPDATE events SET {update_clause} WHERE {where_clause}"
        cur = conn.execute(sql, params)
        conn.commit()
        if cur.rowcount == 0:
            existing = conn.execute(
                f"SELECT {_COL_ACKED_AT}, {_COL_DLQ_AT} FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608 — column names are module-level constants, values parameterized
                (event_id,),
            ).fetchone()
            if existing:
                return (-2, -2)
            return (-1, -1)
        row = conn.execute(
            f"SELECT {_COL_DELIVERY_FAILURE_COUNT}, {_COL_CYCLE_FAILURE_COUNT} FROM events WHERE {_COL_EVENT_ID} = ?",  # nosec B608 — column names are module-level constants, values parameterized
            (event_id,),
        ).fetchone()
        if row:
            return (
                int(row[_COL_DELIVERY_FAILURE_COUNT]),
                int(row[_COL_CYCLE_FAILURE_COUNT]),
            )
        return (-1, -1)
    except Exception:
        conn.rollback()
        raise
```

Key changes:
- Added optional `consumer_id` parameter for consumer-specific failure tracking.
- When `consumer_id` is provided, also increment `consumer_delivery_failure_count`.
- Updated SQL query to include consumer_id in WHERE clause when provided.

### Details

- REQ-010: Consumer-specific failure counter semantics defined and implemented.

## Compatibility considerations

- The `/subscribe` endpoint's query parameters remain unchanged.
- The SSE response format remains unchanged.
- Backward compatibility for `auth_token` must be explicitly tested.

## Security considerations

- Raw token values must never be logged — use `token_fingerprint` instead.
- All unauthorized responses must use HTTP 401 or HTTP 403.

## Rollback considerations

- Revert requires restoring original `nack_event()` single-counter logic.
- The revert is mechanical — no semantic changes beyond restoring original function signatures.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/db.py | Unit: delivery-state verification logic | uv run pytest tests/eventbus/test_eventbus_ack_nack.py -v | New DB tests pass |
| scripts/eventbus/db.py | Static analysis: no credential exposure in logs | uv run bandit -r scripts/eventbus/ -c pyproject.toml | No high/medium findings |
| scripts/eventbus/db.py | Type checking | uv run mypy scripts/eventbus/db.py | No new type errors |

## Completion criteria

- [ ] `_COL_CONSUMER_DELIVERY_FAILURE_COUNT` constant added.
- [ ] Migration logic adds `consumer_delivery_failure_count` column.
- [ ] `nack_event()` accepts optional `consumer_id` parameter.
- [ ] `nack_event()` increments consumer-specific failure count when `consumer_id` provided.
- [ ] All existing tests pass without modification.
- [ ] No new static analysis or type-checking errors are introduced.

## Out of scope

- Changes to the `/subscribe` endpoint's query parameters or HTTP response format.
- Changes to the `broker.py` subscriber lifecycle or disconnect mechanism.
- Changes to the `config.py` replay_batch_size parameter.
- Documentation updates (handled separately per REQ-011).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add consumer failure counter column constant | Pending | — | — | |
| 2 | Update _migrate() to add consumer failure counter column | Pending | — | — | |
| 3 | Update nack_event() to track consumer-specific failures | Pending | — | — | |

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
- **Requirement ID**: REQ-010
- **Source issue**: issues/20260914-102317_eventbus03_consumer-topic-authorization-ack-nack.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260914-172234_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260914-202430
- **Related target files**: scripts/eventbus/db.py
