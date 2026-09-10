## Goal
Switch `subscribe_route.py`'s offset-read path from file-based `read_offset()` to the
new SQLite-backed `consumer_offsets` table (via row 03's `get_consumer_offset()`)
(REQ-005).

## Scope
In scope: the single `if consumer_id and start_seq == 0: start_seq =
read_offset(cfg.offsets_dir, consumer_id)` line inside `subscribe()`. Out of scope:
any other part of `_sse_gen()` (replay fetch, live delivery loop, `finally:
broker.unsubscribe(sub)`) — untouched by this Plan (those are in scope for the
separate backpressure/duplicate-consumer Plan, not this one).

## Assumptions
- `get_consumer_offset(conn, consumer_id) -> int` (row 03) defaults to `0` when no row
  exists, matching `read_offset()`'s current default-to-zero behavior exactly — no
  caller-visible behavior change for a consumer with no prior offset.
- `db` (the SQLite connection) is already available in `subscribe()`'s scope via
  `get_db(request)` — confirmed, no new dependency needed.

## Design decisions
Replace the local `from eventbus.offsets import read_offset` import and its call with
a call to the new `eventbus.db` read function, using the same `db` connection already
obtained via `get_db(request)`. Since this Plan's row 03 function is synchronous and
performs a single indexed `SELECT`, no `run_with_db_lock()` wrapping is required here —
match whatever pattern `ack_event_for_consumer()`'s own read-only helper analogues use
elsewhere in the module (confirm consistency with row 03's final implementation before
finalizing this row).

## Alternatives considered
Keeping `read_offset()` as a fallback when `get_consumer_offset()` returns `0` (to
also check the legacy file in case migration has not yet run) was considered and
rejected: `migrate_legacy_offsets()` (row 03) runs once at startup via `app.py`'s
`lifespan()` (row 06), before any `/subscribe` request can be served, so by the time
this code path runs, `consumer_offsets` is already the authoritative source — a
fallback would silently mask a migration bug rather than surface it.

## Implementation
### Target file
`scripts/eventbus/subscribe_route.py`

### Procedure
1. Remove the local `from eventbus.offsets import read_offset` import (no longer used
   by this file after the change — confirm no other line in this file calls it).
2. Import the new read function from `eventbus.db` (e.g. `get_consumer_offset`).
3. Replace `start_seq = read_offset(cfg.offsets_dir, consumer_id)` with `start_seq =
   get_consumer_offset(db, consumer_id)`.

### Method
Single-line call-site substitution; no structural change to `subscribe()` or
`_sse_gen()`.

### Details
```python
from eventbus.db import get_consumer_offset

async def subscribe(
    request: Request,
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
) -> Any:
    cfg = request.app.state.config
    assert cfg is not None
    broker = get_broker(request)
    db = get_db(request)

    start_seq = since_seq
    if consumer_id and start_seq == 0:
        start_seq = get_consumer_offset(db, consumer_id)
    ...
```
The rest of `subscribe()`/`_sse_gen()` is unchanged.

## Compatibility considerations
`cfg.offsets_dir` is no longer read on this path, but the config field itself is not
removed (still used by `migrate_legacy_offsets()` via `app.py`, row 06, and by
`ack_route.py`'s empty-`consumer_id` fallback, row 04). No client-visible contract
change: `since_seq`/`consumer_id` query parameters behave identically.

## Security considerations
No new input path; `consumer_id` continues to arrive as a validated query parameter,
now bound via a parameterized `SELECT` instead of used as a filename component — this
is a strictly safer input path than the file-based lookup it replaces.

## Rollback considerations
Revert this file's diff to restore the `read_offset()`-based lookup. Since
`offsets_dir` files are never deleted by this Plan, a rollback here works even after
`migrate_legacy_offsets()` has run — the legacy files remain intact as a fallback data
source.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_restart_resume.py -v` (row 10):
  resume-from-offset against the new SQLite-backed store (AC-6).
- `uv run pytest tests/eventbus/test_eventbus_replay_subscribe.py -v` (Reference File,
  regression boundary): confirm this file's other behavior (replay, topic filtering)
  is unaffected.

## Completion criteria
`subscribe()` resolves `start_seq` exclusively via `get_consumer_offset()` for a
non-empty `consumer_id` with `since_seq == 0`; `read_offset()` is no longer imported or
called by this file.

## Out of scope
Any change to `_sse_gen()`'s replay/live-delivery logic, or to the
`finally: broker.unsubscribe(sub)` release path.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace `read_offset()` call with `get_consumer_offset(db, consumer_id)` | Pending | — | — | |
| 2 | Remove the now-unused `read_offset` import | Pending | — | — | |
| 3 | Add or update tests per Validation plan (row 10) | Pending | — | — | |
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
- **Requirement ID**: REQ-005
- **Source issue**: issues/20260907-125042_eb_h01_transactional_ack_offset_delivery_state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-094115_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-092106
- **Related target files**: scripts/eventbus/subscribe_route.py
