## Goal
Replace `ack_route.py`'s `_ack_and_offset()` two-call body (`_ack_event()` then
`write_offset()`) with a single call into `eventbus.db`'s new
`ack_event_for_consumer()` (row 03), so the ACK write and offset advancement commit or
roll back together (REQ-003).

## Scope
In scope: `_do_ack()`'s inner `_ack_and_offset()` closure only. Out of scope: `nack()`
and its `_nack_and_promote()` closure — untouched, per Plan Out-of-Scope (DLQ/NACK
path unrelated to this Requirement).

## Assumptions
- `ack_event_for_consumer(conn, event_id, consumer_id, now)` (row 03) is available and
  returns `(found, newly_acked)`, mirroring `ack_event()`'s existing contract, so the
  surrounding `_do_ack()` response-building logic (lines building `resp["seq"]`, the
  `already_acked`/404 branches) needs no change beyond the call site itself.
- `run_with_db_lock()` continues to wrap the entire `_ack_and_offset()` closure, so no
  additional locking is introduced or removed here.

## Design decisions
`_ack_and_offset()` calls `ack_event_for_consumer(db, event_id, consumer_id, now)`
instead of `_ack_event(db, event_id, now)` followed by a separate `write_offset(...)`
call — collapsing two independent, uncoordinated writes into the one transactional
function row 03 provides. The `consumer_id` empty-string case (anonymous connection,
no offset tracking) must still be handled: when `consumer_id` is empty,
`ack_event_for_consumer()` should still ack in `consumer_delivery`... but per the
Plan's per-consumer model, an empty `consumer_id` has no meaningful per-consumer
delivery/offset record. Confirm during implementation whether `_ack_and_offset()`
should skip the new function entirely for an empty `consumer_id` and fall back to a
consumer_id-less path, or whether `ack_event_for_consumer()` itself handles an empty
key gracefully — this must be resolved against `ack_event()`'s current global-flag
behavior (which requires no `consumer_id` at all) before finalizing this row, since the
Plan's row 03 design assumes a non-empty `consumer_id` key.

## Alternatives considered
Keeping `_ack_event()` + `write_offset()` as a fallback path for an empty `consumer_id`
(dual-path: transactional for non-empty, legacy for empty) was considered. This is the
approach recommended for implementation, since the per-consumer tables are keyed by
`consumer_id` and an empty key does not represent a real consumer identity — this
avoids inserting meaningless rows keyed by `""` into `consumer_delivery`/
`consumer_offsets`.

## Implementation
### Target file
`scripts/eventbus/ack_route.py`

### Procedure
1. Import `ack_event_for_consumer` from `eventbus.db` alongside the existing
   `ack_event as _ack_event` import (keep `_ack_event` import only if the empty-
   `consumer_id` fallback path, above, retains it — otherwise remove the now-unused
   import).
2. Remove the `from eventbus.offsets import write_offset` import if no longer used by
   this file after the change (confirm no other function in this file calls
   `write_offset` directly).
3. Rewrite `_ack_and_offset()`'s body: when `consumer_id` is non-empty, call
   `ack_event_for_consumer(db, event_id, consumer_id, now)`; when empty, preserve
   today's `_ack_event(db, event_id, now)`-only behavior (no offset write, matching
   current behavior where `write_offset()` is only called `if consumer_id and
   newly_acked`).

### Method
Direct function-body edit; no new class or module-level state.

### Details
```python
def _ack_and_offset() -> tuple[bool, bool, int | None]:
    """Acknowledge an event and advance its consumer offset, transactionally."""
    now = now_iso()
    if consumer_id:
        found, newly_acked = ack_event_for_consumer(db, event_id, consumer_id, now)
        seq: int | None = None
        if newly_acked:
            row = db.execute(
                "SELECT seq FROM events WHERE event_id = ?", (event_id,)
            ).fetchone()
            seq = int(row["seq"]) if row else None
        return (found, newly_acked, seq)
    found, newly_acked = _ack_event(db, event_id, now)
    return (found, newly_acked, None)
```
The `seq` re-lookup after `ack_event_for_consumer()` is only needed for the response
payload (`resp["seq"] = seq`); confirm whether `ack_event_for_consumer()` can instead
return `seq` directly (row 03) to avoid this second query — prefer that if row 03's
signature can be extended to return `(found, newly_acked, seq)` without breaking its
own contract used elsewhere.

## Compatibility considerations
The route's external contract (`resp["seq"]`, `already_acked`, 404 on not-found) is
unchanged — only the internal write mechanism changes. `write_offset()` itself is not
deleted (per Plan Out-of-Scope) and remains available for any other caller, but this
file no longer calls it for the non-empty-`consumer_id` path.

## Security considerations
No new input path; `event_id`/`consumer_id` continue to arrive as validated query/path
parameters, unchanged from today.

## Rollback considerations
Revert this file's diff to restore the two-call, two-commit behavior. Since row 03's
new tables remain additive and unused by any other caller if this file is reverted
alone, no data cleanup is required for a clean rollback.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_crash_ack.py -v` (row 09): a failure
  injected into the offset-advancement step after the delivery-state write must leave
  neither committed (AC-3) — this is the primary regression test for this row's change.
- `uv run pytest tests/eventbus/test_eventbus_ack_endpoint.py -v` (Reference File,
  regression boundary): must continue passing unmodified against the retained legacy
  `read_offset()` path for any test that does not go through this route's non-empty-
  `consumer_id` branch.

## Completion criteria
`_ack_and_offset()` calls exactly one function for the non-empty-`consumer_id` case
(no separate `write_offset()` call remains reachable on that path); the
forced-failure test (row 09) confirms the delivery write is rolled back when the
offset write step fails.

## Out of scope
`nack()`/`_nack_and_promote()` — unrelated to REQ-003, untouched.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace `_ack_and_offset()`'s two-call body with `ack_event_for_consumer()` (non-empty consumer_id) | Pending | — | — | |
| 2 | Preserve `_ack_event()`-only behavior for empty `consumer_id` | Pending | — | — | |
| 3 | Add or update tests per Validation plan (row 09) | Pending | — | — | |
| 4 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Source issue**: issues/20260907-125042_eb_h01_transactional_ack_offset_delivery_state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-094115_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-092106
- **Related target files**: scripts/eventbus/ack_route.py
