## Goal

Switch `scripts/eventbus/subscribe_route.py`'s offset-read path from file-based `read_offset()` to the new SQLite-backed offset table (`consumer_offsets`), enabling consumers to resume from their last-committed offset regardless of whether it was stored in the legacy file system or the new SQLite store.

## Scope

- Replace the `read_offset(cfg.offsets_dir, consumer_id)` call in `subscribe()` with a read from the new `consumer_offsets` SQLite table.
- Add a helper function in `eventbus.db` for reading the offset from SQLite (or reuse an existing function).
- Handle the case where the offset doesn't exist yet (return 0, same as current `read_offset()` fallback).

## Assumptions

- The `consumer_offsets` table exists (created by the migration in the related procedure document).
- The `consumer_id` parameter is already validated as non-empty before the offset lookup.
- The `start_seq == 0` condition triggers the offset recovery path (same as current behavior).

## Design decisions

- **SQLite-first**: Read from `consumer_offsets` first; if no row exists, fall back to the legacy file-based `read_offset()` for backward compatibility during migration.
- **Lazy migration**: If the offset is found in the file system but not in SQLite, migrate it silently (the startup migration should handle this, but a runtime fallback is safer).
- **Zero default**: When no offset exists in either source, return 0 (same as current `read_offset()` fallback).

## Alternatives considered

- **Strict SQLite-only**: Require the startup migration to complete before allowing subscriptions. Rejected because the migration must be idempotent and the system should work even if the migration hasn't run yet.
- **Dual-read with conflict resolution**: Read from both sources and prefer the newer one. Rejected because the two sources should converge after migration; dual-read adds complexity without clear benefit.

## Implementation

### Target file

`scripts/eventbus/subscribe_route.py`

### Procedure

1. Replace the `read_offset(cfg.offsets_dir, consumer_id)` call with a SQLite-backed read.
2. Add a helper function in `eventbus.db` for reading the offset from SQLite (if not already added).
3. Keep the legacy `read_offset()` import for backward-compatibility fallback.

### Method

#### Step 1: Replace the offset read call

Change lines 25 and 33-34:
```python
async def subscribe(
    request: Request,
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
) -> Any:
    """Subscribe to events via SSE with optional topic filtering and offset recovery."""
    from eventbus.offsets import read_offset  # noqa: PLC0415

    cfg = request.app.state.config
    assert cfg is not None
    broker = get_broker(request)
    db = get_db(request)

    start_seq = since_seq
    if consumer_id and start_seq == 0:
        start_seq = read_offset(cfg.offsets_dir, consumer_id)
```

To:
```python
async def subscribe(
    request: Request,
    topic: list[str] = Query(default=[]),
    since_seq: int = Query(default=0, ge=0),
    consumer_id: str = Query(default=""),
) -> Any:
    """Subscribe to events via SSE with optional topic filtering and offset recovery."""
    from eventbus.offsets import read_offset  # noqa: PLC0415 — retained for legacy fallback

    cfg = request.app.state.config
    assert cfg is not None
    broker = get_broker(request)
    db = get_db(request)

    start_seq = since_seq
    if consumer_id and start_seq == 0:
        # Try SQLite-backed offset first, then fall back to legacy file-based
        start_seq = _get_offset_from_sqlite(db, consumer_id)
        if start_seq == 0:
            start_seq = read_offset(cfg.offsets_dir, consumer_id)
```

#### Step 2: Add helper function

Add after the `subscribe()` function (after line 89):

```python
def _get_offset_from_sqlite(
    db: Any,
    consumer_id: str,
) -> int:
    """Read the last-committed sequence offset for a consumer from the SQLite store.

    Returns 0 if no offset exists for this consumer.
    """
    try:
        row = db.execute(
            "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
            (consumer_id,),
        ).fetchone()
        if row:
            return int(row["offset"])
    except Exception:
        # Table doesn't exist yet or query failed — fall through to legacy path
        pass
    return 0
```

### Details

The key changes are:

1. **Offset read priority**: The new flow reads from `consumer_offsets` first, then falls back to the legacy file-based `read_offset()` if the SQLite read returns 0. This ensures:
   - Consumers that have been migrated to the SQLite store resume correctly.
   - Consumers that haven't been migrated yet continue to work via the legacy path.
   - After the startup migration completes, only the SQLite path is used.

2. **Helper function**: `_get_offset_from_sqlite()` encapsulates the SQLite read logic, providing a clean separation between the new and legacy paths. It returns 0 on any exception (table doesn't exist, query fails, etc.), which triggers the legacy fallback.

3. **Legacy import retention**: The `from eventbus.offsets import read_offset` import is kept with a comment noting it's retained for legacy fallback. This avoids breaking any callers that might still need the legacy path.

4. **Zero default preservation**: Both paths return 0 when no offset exists, maintaining the same semantics as the current code.

## Compatibility considerations

- The `consumer_id` parameter is already accepted as a `Query` param in the current code — no new parameters needed.
- The `start_seq == 0` condition triggers the offset recovery path (same as current behavior).
- The `finally: broker.unsubscribe(sub)` release path is unchanged.
- The SSE generator loop (`while True`) is unchanged.

## Security considerations

- No new authentication or authorization boundaries introduced.
- SQL values are bound via `?` placeholders — no injection risk.
- The `consumer_id` parameter is validated as non-empty by the caller (not the offset read itself).

## Rollback considerations

- To rollback: restore the original `read_offset(cfg.offsets_dir, consumer_id)` call.
- The rollback restores the pre-change state where offsets are always read from the file system.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/subscribe_route.py` | Structural verification | Read file, confirm SQLite-first read path | Two-path read: SQLite first, then legacy fallback |
| `tests/eventbus/test_eventbus_restart_resume.py` | Integration test | `uv run pytest tests/eventbus/test_eventbus_restart_resume.py -v` | Resume-from-offset works against the SQLite-backed store |
| Full EventBus suite | Regression | `uv run pytest tests/eventbus/ -v` | All pass, including retained-legacy-path tests |

## Completion criteria

- Offset read prefers SQLite `consumer_offsets` over legacy file-based `read_offset()`.
- Fallback to legacy path when SQLite read returns 0.
- Helper function `_get_offset_from_sqlite()` handles exceptions gracefully.
- No other code paths modified.

## Out of scope

- Modifying the SSE generator loop (`_sse_gen`) — covered by a separate procedure document.
- Adding DDL to schema files — covered by separate procedure documents.
- Adding the disconnect signal mechanism — covered by a separate procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Replace read_offset call with SQLite-first path | Completed | — | — | Actual uses get_consumer_offset() directly from eventbus.db |
| 2 | Add _get_offset_from_sqlite helper | N/A | — | — | Not needed — get_consumer_offset() in db.py serves this role |
| 3 | Run validation (pytest + structural check) | Completed | — | — | |

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
- **Generated at**: 20260910-161316
- **Related target files**: scripts/eventbus/subscribe_route.py
