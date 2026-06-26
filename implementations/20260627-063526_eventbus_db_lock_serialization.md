## Goal

Verify SQLite shared connection thread-safety in the Event Bus and add DB access serialization if needed. Confirm that all DB operations are properly serialized to prevent data races when `asyncio.to_thread()` executes them in FastAPI's thread pool workers.

## Scope

**In-Scope**:
- Confirm whether Event Bus routes use `async def` or `def` and how DB operations are executed
- Verify if DB code can run inside FastAPI's thread pool (via `asyncio.to_thread()`)
- Add `_db_lock` acquisition to all `asyncio.to_thread()` callables in app.py that perform DB operations
- Add stress tests for concurrent: publish, replay, subscribe, ack, DLQ promotion
- Update known-issues doc to resolve the FastAPI thread pool item

**Out-of-Scope**:
- Replacing SQLite with another database
- Distributed Event Bus clustering

## Assumptions

1. All DB operations in app.py should use `_db_lock` from db.py before executing on the shared connection
2. The lock acquisition must be inside `asyncio.to_thread()` callables, not outside (to avoid blocking the event loop)
3. Stress tests will simulate concurrent requests to verify no race conditions occur

## Implementation

### Target file: scripts/eventbus/app.py

**Procedure**: Add `_db_lock` acquisition to all DB operations.

**Method**: Modify app.py to import `get_db_lock` and acquire it inside each `asyncio.to_thread()` callable.

**Details**:
1. Import `get_db_lock` from db.py in app.py
2. For each `asyncio.to_thread()` callable that accesses the shared connection, acquire the lock using a context manager (`with get_db_lock():`)
3. Affected callables:
   - `_check` in health route (line 116-119)
   - `insert_event` in publish route (line 182-190)
   - `fetch_events_since` in replay route (line 231-233)
   - `_count_events_since` in replay route (line 236)
   - `_fetch_replay` in subscribe route (line 274-288)
   - `count_dlq` in dlq_list route (line 324)
   - `fetch_dlq` in dlq_list route (line 325)
   - `requeue_event` in dlq_requeue route (line 337)
   - `_ack_and_offset` in ack route (line 355-371)
   - `_ack_and_offset` in ack_event route (line 387-403)
   - `_nack_and_promote` in nack route (line 421-432)

### Target file: scripts/eventbus/dlq.py

**Procedure**: Verify internal locking mechanisms.

**Method**: Check if `sweep_orphans` acquires its own locks.

**Details**:
1. Check dlq.py for internal locking mechanisms
2. If DLQ loop `_dlq_loop` needs lock acquisition, add it inside its `asyncio.to_thread()` callable

### Target file: tests/test_eventbus_concurrent.py (new)

**Procedure**: Add stress tests for concurrent DB operations.

**Method**: Create new test file with concurrent stress tests.

**Details**:
1. Test concurrent publish requests (10+ simultaneous)
2. Test concurrent ack requests on same event_id
3. Test concurrent replay/subscribe with overlapping time ranges
4. Test concurrent DLQ requeue operations
5. Verify no SQLite lock errors or data corruption

### Target file: docs/06_eventbus_90_inconsistencies_and_known_issues.md

**Procedure**: Update known-issues doc to resolve FastAPI thread pool item.

**Method**: Resolve the "FastAPI thread pool worker usage" item (line 23).

**Details**:
1. Document the final DB access model: shared connection + `_db_lock` serialization via `asyncio.to_thread()`
2. Mark item as resolved with explanation

## Validation plan

| Target File/Module | Testing Strategy | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/app.py | Verify all `asyncio.to_thread()` callables acquire `_db_lock` | Check each callable for lock acquisition | All DB operations properly serialized |
| tests/test_eventbus_concurrent.py (new) | Run concurrent stress test | Run pytest | No SQLite errors, no data corruption |
| 06_eventbus_90_inconsistencies_and_known_issues.md | Verify FastAPI thread pool item resolved | Check for updated resolution | Item marked as resolved with explanation |

## Risks

- **Risk**: Adding `_db_lock` acquisition could introduce deadlocks if lock is acquired in wrong order or nested contexts | **Likelihood**: Low-Medium | **Mitigation**: Lock is only acquired inside `asyncio.to_thread()` callables, never outside. All lock acquisitions are via context manager (`with get_db_lock():`) ensuring release. No nested lock acquisition possible since all operations are serialized at the outer level. | False
- **Risk**: DLQ loop `_dlq_loop` may need separate lock handling since it runs as a background task | **Likelihood**: Low | **Mitigation**: `sweep_orphans` in dlq.py acquires the same shared connection; lock acquisition inside its `asyncio.to_thread()` callable will serialize it with other operations. | False
- **Risk**: Lock contention under high concurrent load could degrade performance | **Likelihood**: Medium | **Mitigation**: SQLite WAL mode already serializes writers; adding `_db_lock` is a belt-and-suspenders approach. If contention becomes an issue, consider per-operation connections or connection pooling. | False
