# Implementation: scripts/eventbus/db.py

## Goal

Fix SQL injection vulnerability in `fetch_events_since()` and `fetch_dlq()`, unify transaction handling across all DB functions, eliminate duplicated two-step existence-check patterns, reduce query duplication, and extract column name constants.

## Scope

- Modify `scripts/eventbus/db.py` only.
- Fix SQL injection in `fetch_events_since()` (line 425) — replace `f" LIMIT {limit} OFFSET {offset}"` with parameterized query.
- Fix SQL injection in `fetch_dlq()` (line 441) — same approach.
- Add explicit `try/finally` with `conn.rollback()` to `ack_event()` around the UPDATE+SELECT sequence.
- Add explicit `try/finally` with `conn.rollback()` to `nack_event()` around the UPDATE+SELECT sequence.
- Remove pre-check SELECT from `requeue_event()` — rely on UPDATE's WHERE clause and rowcount.
- Replace pre-check SELECT in `redeliver_event()` with UPDATE rowcount check.
- Unify timestamp handling: add `now` parameter to `redeliver_event()`, remove `strftime('now')` from SQL.
- Extract column name constants at module level.
- Update all SQL strings to use extracted constants instead of inline column names.

## Assumptions

- The public API contract requires all function signatures to remain identical except `redeliver_event()` which gains a `now` parameter.
- `check_same_thread=False` + `get_db_lock()` pattern is sufficient for asyncio.to_thread() concurrency.
- Column names in schema.sql are stable and will not change during this refactor.
- Callers of `redeliver_event()` can provide the `now` parameter.

## Design decisions

- **SQL injection fix**: Replace string interpolation in `fetch_events_since()` and `fetch_dlq()` with conditional query construction using `?` placeholders. Validate that `limit >= 0` and `offset >= 0` at the Python level before constructing the query.
- **Transaction unification**: Wrap all functions that modify state (UPDATE/INSERT/DELETE) in explicit transactions using `conn.commit()` and `conn.rollback()`. For functions that currently do UPDATE → commit → SELECT, replace with UPDATE → SELECT in a single transaction.
- **Pre-check elimination**: For `requeue_event()`, remove the initial SELECT entirely. The UPDATE's WHERE clause (`dlq_at IS NOT NULL`) already enforces the constraint. Use `cur.rowcount > 0` to determine success/failure. For `redeliver_event()`, use the UPDATE's rowcount to determine success/failure instead of the pre-check SELECT.
- **Timestamp unification**: Add `now: str | None = None` parameter to `redeliver_event()`. If `now` is None, fall back to `strftime('now')` for backward compatibility.
- **Column name constant extraction**: Define module-level constants for frequently used column names: `_COL_DELIVERY_FAILURE_COUNT = "delivery_failure_count"`, `_COL_CYCLE_FAILURE_COUNT = "cycle_failure_count"`, `_COL_DLQ_AT = "dlq_at"`, `_COL_DLQ_REQUEUE_COUNT = "dlq_requeue_count"`, `_COL_ACKED_AT = "acked_at"`, etc.

## Alternatives considered

- **Keep both liveness methods**: Would preserve backward compatibility but perpetuates the inconsistency bug where callers cannot know which liveness model applies.
- **Deprecate rather than remove**: Would allow gradual migration but adds maintenance burden for deprecated methods.

## Implementation

### Target file

`scripts/eventbus/db.py`

### Procedure

1. Extract column name constants at module level.
2. Replace inline column names with constants in all SQL strings.
3. Fix SQL injection in `fetch_events_since()` — replace `f" LIMIT {limit} OFFSET {offset}"` with parameterized query.
4. Fix SQL injection in `fetch_dlq()` — same approach.
5. Add explicit `try/finally` with `conn.rollback()` to `ack_event()` around the UPDATE+SELECT sequence.
6. Add explicit `try/finally` with `conn.rollback()` to `nack_event()` around the UPDATE+SELECT sequence.
7. Remove pre-check SELECT from `requeue_event()` — rely on UPDATE's WHERE clause and rowcount.
8. Replace pre-check SELECT in `redeliver_event()` with UPDATE rowcount check.
9. Unify timestamp handling: add `now` parameter to `redeliver_event()`, remove `strftime('now')` from SQL.

### Method

```python
# Step 1: Extract column name constants at module level
# After line 26 (_DEFAULT_BUSY_TIMEOUT_MS = 30_000):
_COL_DELIVERY_FAILURE_COUNT = "delivery_failure_count"
_COL_CYCLE_FAILURE_COUNT = "cycle_failure_count"
_COL_DLQ_AT = "dlq_at"
_COL_DLQ_REQUEUE_COUNT = "dlq_requeue_count"
_COL_ACKED_AT = "acked_at"
_COL_SEQ = "seq"
_COL_EVENT_ID = "event_id"
_COL_CONSUMER_ID = "consumer_id"
_COL_OFFSET = "offset"

# Step 2: Replace inline column names with constants in all SQL strings
# In _migrate() (lines 97-122):
# Before:
#     for col in ("delivery_failure_count", "dlq_requeue_count"):
#         ...
#     for col in ("cycle_failure_count", "redelivered_from"):
#         ...
# After:
#     for col in (_COL_DELIVERY_FAILURE_COUNT, _COL_DLQ_REQUEUE_COUNT):
#         ...
#     for col in (_COL_CYCLE_FAILURE_COUNT, "redelivered_from"):
#         ...

# In ack_event() (line 184):
# Before:
#     "UPDATE events SET acked_at = ? WHERE event_id = ? AND acked_at IS NULL"
# After:
#     f"UPDATE events SET {_COL_ACKED_AT} = ? WHERE {_COL_EVENT_ID} = ? AND {_COL_ACKED_AT} IS NULL"

# In nack_event() (line 212):
# Before:
#     "UPDATE events SET delivery_failure_count = delivery_failure_count + 1, cycle_failure_count = cycle_failure_count + 1 WHERE event_id = ? AND acked_at IS NULL AND dlq_at IS NULL"
# After:
#     f"UPDATE events SET {_COL_DELIVERY_FAILURE_COUNT} = {_COL_DELIVERY_FAILURE_COUNT} + 1, {_COL_CYCLE_FAILURE_COUNT} = {_COL_CYCLE_FAILURE_COUNT} + 1 WHERE {_COL_EVENT_ID} = ? AND {_COL_ACKED_AT} IS NULL AND {_COL_DLQ_AT} IS NULL"

# In nack_event() (line 219):
# Before:
#     "SELECT acked_at, dlq_at FROM events WHERE event_id = ?"
# After:
#     f"SELECT {_COL_ACKED_AT}, {_COL_DLQ_AT} FROM events WHERE {_COL_EVENT_ID} = ?"

# In nack_event() (line 227):
# Before:
#     "SELECT delivery_failure_count, cycle_failure_count FROM events WHERE event_id = ?"
# After:
#     f"SELECT {_COL_DELIVERY_FAILURE_COUNT}, {_COL_CYCLE_FAILURE_COUNT} FROM events WHERE {_COL_EVENT_ID} = ?"

# In requeue_event() (line 456):
# Before:
#     "SELECT 1 FROM events WHERE event_id = ? AND dlq_at IS NOT NULL"
# After:
#     f"SELECT 1 FROM events WHERE {_COL_EVENT_ID} = ? AND {_COL_DLQ_AT} IS NOT NULL"

# In requeue_event() (line 462):
# Before:
#     "UPDATE events SET dlq_requeue_count = dlq_requeue_count + 1, dlq_at = NULL WHERE event_id = ? AND dlq_at IS NOT NULL"
# After:
#     f"UPDATE events SET {_COL_DLQ_REQUEUE_COUNT} = {_COL_DLQ_REQUEUE_COUNT} + 1, {_COL_DLQ_AT} = NULL WHERE {_COL_EVENT_ID} = ? AND {_COL_DLQ_AT} IS NOT NULL"

# In redeliver_event() (line 481):
# Before:
#     "SELECT delivery_failure_count FROM events WHERE event_id = ? AND dlq_at IS NOT NULL"
# After:
#     f"SELECT {_COL_DELIVERY_FAILURE_COUNT} FROM events WHERE {_COL_EVENT_ID} = ? AND {_COL_DLQ_AT} IS NOT NULL"

# In redeliver_event() (line 489):
# Before:
#     "UPDATE events SET dlq_requeue_count = dlq_requeue_count + 1 WHERE event_id = ? AND dlq_at IS NOT NULL"
# After:
#     f"UPDATE events SET {_COL_DLQ_REQUEUE_COUNT} = {_COL_DLQ_REQUEUE_COUNT} + 1 WHERE {_COL_EVENT_ID} = ? AND {_COL_DLQ_AT} IS NOT NULL"

# In redeliver_event() (line 493-494):
# Before:
#     "INSERT INTO events (event_id, topic, payload, producer, published_at, delivery_failure_count, cycle_failure_count, redelivered_from) "
#     "SELECT ?, topic, payload, producer, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'), delivery_failure_count, 0, ? "
#     "FROM events WHERE event_id = ?"
# After:
#     f"INSERT INTO events ({_COL_EVENT_ID}, topic, payload, producer, published_at, {_COL_DELIVERY_FAILURE_COUNT}, {_COL_CYCLE_FAILURE_COUNT}, redelivered_from) "
#     f"SELECT ?, topic, payload, producer, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'), {_COL_DELIVERY_FAILURE_COUNT}, 0, ? "
#     f"FROM events WHERE {_COL_EVENT_ID} = ?"

# Step 3: Fix SQL injection in fetch_events_since()
# In fetch_events_since() (line 424-426):
# Before:
#     if limit is not None and offset is not None:
#         sql += f" LIMIT {limit} OFFSET {offset}"
# After:
#     if limit is not None and offset is not None:
#         # Validate bounds before parameterizing
#         if limit < 0 or offset < 0:
#             raise ValueError(f"limit and offset must be non-negative, got limit={limit!r}, offset={offset!r}")
#         sql += " LIMIT ? OFFSET ?"
#         params = params + (limit, offset)

# Step 4: Fix SQL injection in fetch_dlq()
# In fetch_dlq() (line 440-441):
# Before:
#     if limit is not None and offset is not None:
#         sql += f" LIMIT {limit} OFFSET {offset}"
# After:
#     if limit is not None and offset is not None:
#         # Validate bounds before parameterizing
#         if limit < 0 or offset < 0:
#             raise ValueError(f"limit and offset must be non-negative, got limit={limit!r}, offset={offset!r}")
#         sql += " LIMIT ? OFFSET ?"
#         params = params + (limit, offset)

# Step 5: Add explicit try/finally with conn.rollback() to ack_event()
# In ack_event() (lines 183-197):
# Before:
#     cur = conn.execute(
#         "UPDATE events SET acked_at = ? WHERE event_id = ? AND acked_at IS NULL",
#         (now, event_id),
#     )
#     conn.commit()
#     newly_acked = cur.rowcount > 0
#     if newly_acked:
#         return True, True
#     exists = conn.execute(
#         "SELECT 1 FROM events WHERE event_id = ?", (event_id,)
#     ).fetchone()
#     if exists:
#         return True, False
#     return False, False
# After:
#     try:
#         cur = conn.execute(
#             f"UPDATE events SET {_COL_ACKED_AT} = ? WHERE {_COL_EVENT_ID} = ? AND {_COL_ACKED_AT} IS NULL",
#             (now, event_id),
#         )
#         conn.commit()
#         newly_acked = cur.rowcount > 0
#         if newly_acked:
#             return True, True
#         exists = conn.execute(
#             f"SELECT 1 FROM events WHERE {_COL_EVENT_ID} = ?", (event_id,)
#         ).fetchone()
#         if exists:
#             return True, False
#         return False, False
#     except Exception:
#         conn.rollback()
#         raise

# Step 6: Add explicit try/finally with conn.rollback() to nack_event()
# In nack_event() (lines 211-232):
# Before:
#     cur = conn.execute(
#         "UPDATE events SET delivery_failure_count = delivery_failure_count + 1, cycle_failure_count = cycle_failure_count + 1 WHERE event_id = ? AND acked_at IS NULL AND dlq_at IS NULL",
#         (event_id,),
#     )
#     conn.commit()
#     if cur.rowcount == 0:
#         existing = conn.execute(
#             "SELECT acked_at, dlq_at FROM events WHERE event_id = ?",
#             (event_id,),
#         ).fetchone()
#         if existing:
#             return (-2, -2)
#         return (-1, -1)
#     row = conn.execute(
#         "SELECT delivery_failure_count, cycle_failure_count FROM events WHERE event_id = ?",
#         (event_id,),
#     ).fetchone()
#     if row:
#         return (int(row["delivery_failure_count"]), int(row["cycle_failure_count"]))
#     return (-1, -1)
# After:
#     try:
#         cur = conn.execute(
#             f"UPDATE events SET {_COL_DELIVERY_FAILURE_COUNT} = {_COL_DELIVERY_FAILURE_COUNT} + 1, {_COL_CYCLE_FAILURE_COUNT} = {_COL_CYCLE_FAILURE_COUNT} + 1 WHERE {_COL_EVENT_ID} = ? AND {_COL_ACKED_AT} IS NULL AND {_COL_DLQ_AT} IS NULL",
#             (event_id,),
#         )
#         conn.commit()
#         if cur.rowcount == 0:
#             existing = conn.execute(
#                 f"SELECT {_COL_ACKED_AT}, {_COL_DLQ_AT} FROM events WHERE {_COL_EVENT_ID} = ?",
#                 (event_id,),
#             ).fetchone()
#             if existing:
#                 return (-2, -2)
#             return (-1, -1)
#         row = conn.execute(
#             f"SELECT {_COL_DELIVERY_FAILURE_COUNT}, {_COL_CYCLE_FAILURE_COUNT} FROM events WHERE {_COL_EVENT_ID} = ?",
#             (event_id,),
#         ).fetchone()
#         if row:
#             return (int(row[_COL_DELIVERY_FAILURE_COUNT]), int(row[_COL_CYCLE_FAILURE_COUNT]))
#         return (-1, -1)
#     except Exception:
#         conn.rollback()
#         raise

# Step 7: Remove pre-check SELECT from requeue_event()
# In requeue_event() (lines 455-466):
# Before:
#     row = conn.execute(
#         "SELECT 1 FROM events WHERE event_id = ? AND dlq_at IS NOT NULL",
#         (event_id,),
#     ).fetchone()
#     if not row:
#         return False
#     cur = conn.execute(
#         "UPDATE events SET dlq_requeue_count = dlq_requeue_count + 1, dlq_at = NULL WHERE event_id = ? AND dlq_at IS NOT NULL",
#         (event_id,),
#     )
#     conn.commit()
#     return cur.rowcount > 0
# After:
#     cur = conn.execute(
#         f"UPDATE events SET {_COL_DLQ_REQUEUE_COUNT} = {_COL_DLQ_REQUEUE_COUNT} + 1, {_COL_DLQ_AT} = NULL WHERE {_COL_EVENT_ID} = ? AND {_COL_DLQ_AT} IS NOT NULL",
#         (event_id,),
#     )
#     conn.commit()
#     return cur.rowcount > 0

# Step 8: Replace pre-check SELECT in redeliver_event() with UPDATE rowcount check
# In redeliver_event() (lines 480-499):
# Before:
#     original_row = conn.execute(
#         "SELECT delivery_failure_count FROM events WHERE event_id = ? AND dlq_at IS NOT NULL",
#         (event_id,),
#     ).fetchone()
#     if not original_row:
#         return (False, None)
#     new_event_id = uuid.uuid4().hex
#     conn.execute(
#         "UPDATE events SET dlq_requeue_count = dlq_requeue_count + 1 WHERE event_id = ? AND dlq_at IS NOT NULL",
#         (event_id,),
#     )
#     conn.execute(
#         "INSERT INTO events (event_id, topic, payload, producer, published_at, delivery_failure_count, cycle_failure_count, redelivered_from) "
#         "SELECT ?, topic, payload, producer, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'), delivery_failure_count, 0, ? "
#         "FROM events WHERE event_id = ?",
#         (new_event_id, event_id, event_id),
#     )
#     conn.commit()
#     return (True, new_event_id)
# After:
#     new_event_id = uuid.uuid4().hex
#     cur = conn.execute(
#         f"UPDATE events SET {_COL_DLQ_REQUEUE_COUNT} = {_COL_DLQ_REQUEUE_COUNT} + 1 WHERE {_COL_EVENT_ID} = ? AND {_COL_DLQ_AT} IS NOT NULL",
#         (event_id,),
#     )
#     if cur.rowcount == 0:
#         return (False, None)
#     conn.execute(
#         f"INSERT INTO events ({_COL_EVENT_ID}, topic, payload, producer, published_at, {_COL_DELIVERY_FAILURE_COUNT}, {_COL_CYCLE_FAILURE_COUNT}, redelivered_from) "
#         f"SELECT ?, topic, payload, producer, strftime('%Y-%m-%dT%H:%M:%SZ', 'now'), {_COL_DELIVERY_FAILURE_COUNT}, 0, ? "
#         f"FROM events WHERE {_COL_EVENT_ID} = ?",
#         (new_event_id, event_id, event_id),
#     )
#     conn.commit()
#     return (True, new_event_id)

# Step 9: Unify timestamp handling — add now parameter to redeliver_event()
# In redeliver_event() signature (line 469):
# Before:
#     def redeliver_event(conn: sqlite3.Connection, event_id: str) -> tuple[bool, str | None]:
# After:
#     def redeliver_event(conn: sqlite3.Connection, event_id: str, now: str | None = None) -> tuple[bool, str | None]:
```

### Details

- Line numbers are approximate — verify against current source before applying changes.
- Need to carefully reconcile the behavioral differences between the old and new implementations — the plan explicitly notes these differences must be reconciled during migration.
- The `strftime('now')` call in `redeliver_event()` must be replaced with the `now` parameter when provided, falling back to `strftime('now')` when `now` is None for backward compatibility.

## Compatibility considerations

- **Breaking change** for consumers of `redeliver_event()` that don't pass the `now` parameter. The parameter has a default value of `None`, so it's backward compatible but callers should update to pass `now` explicitly.
- **No breaking change** for existing callers of other functions — the method signatures remain compatible.

## Security considerations

- **Critical**: Fixing SQL injection in `fetch_events_since()` and `fetch_dlq()` eliminates a production security risk — any caller controlling `limit` or `offset` parameters can inject SQL.
- No new security surface introduced by adding transaction management or eliminating pre-checks.

## Rollback considerations

- Revert the column name constant extraction and inline column names.
- If the SQL injection fix causes unexpected behavior, investigate further before reverting.
- If the transaction rollback logic causes issues, remove the `try/except` blocks and restore the original commit pattern.

## Validation plan

| Target | Strategy | Tool / Command | Expected Outcome |
|--------|----------|----------------|------------------|
| SQL injection fix | Unit test | `uv run pytest tests/eventbus/test_eventbus_db.py -v -k fetch` | No SQL injection; tests pass |
| Transaction safety | Unit test | `uv run pytest tests/eventbus/test_eventbus_ack_nack.py -v -k ack,nack` | Correct return values under concurrency |
| DLQ/requeue/redeliver behavior | Integration test | `uv run pytest tests/eventbus/test_eventbus_dlq.py -v -k requeue,redeliver` | Returns correct values for non-DLQ events |
| Type checking | Static | Type checker against modified file | No type errors |
| Lint checking | Static | Lint tool against modified file | No lint errors |

## Completion criteria

- [ ] Column name constants extracted at module level.
- [ ] All SQL strings use extracted constants instead of inline column names.
- [ ] SQL injection fixed in `fetch_events_since()` and `fetch_dlq()`.
- [ ] Explicit `try/finally` with `conn.rollback()` added to `ack_event()` and `nack_event()`.
- [ ] Pre-check SELECT removed from `requeue_event()`.
- [ ] Pre-check SELECT replaced with UPDATE rowcount check in `redeliver_event()`.
- [ ] `now` parameter added to `redeliver_event()`, `strftime('now')` removed from SQL.
- [ ] Existing tests pass without modification.
- [ ] No type/lint regressions.

## Out of scope

- Modifying `scripts/eventbus/schema.sql` — schema unchanged per Out-of-Scope constraints.
- Modifying `tests/eventbus/test_eventbus_db.py` — handled by a separate implementation procedure document.
- Modifying `tests/eventbus/test_eventbus_dlq.py` — handled by a separate implementation procedure document.
- Modifying `tests/eventbus/test_eventbus_publish_contract.py` — handled by a separate implementation procedure document.
- Modifying `tests/eventbus/test_eventbus_ack_nack.py` — handled by a separate implementation procedure document.
- Modifying `tests/eventbus/test_eventbus_restart_resume.py` — handled by a separate implementation procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extract column name constants | Pending | — | — | |
| 2 | Replace inline column names with constants | Pending | — | — | |
| 3 | Fix SQL injection in fetch_events_since() | Pending | — | — | |
| 4 | Fix SQL injection in fetch_dlq() | Pending | — | — | |
| 5 | Add try/finally to ack_event() | Pending | — | — | |
| 6 | Add try/finally to nack_event() | Pending | — | — | |
| 7 | Remove pre-check from requeue_event() | Pending | — | — | |
| 8 | Replace pre-check in redeliver_event() | Pending | — | — | |
| 9 | Unify timestamp handling | Pending | — | — | |
| 10 | Run validation sequence (rules/toolchain.md) | Pending | — | — | |

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
- **Requirement ID**: REQ-001 through REQ-012
- **Source issue**: issues/20260911-221345_refactor_eventbus_db_fix_sql_injection_unify_transactions.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260911-235808_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260912-005846
- **Related target files**: scripts/eventbus/db.py
