## Goal

Add `get_resume_position(conn, consumer_id)` function to compute the reconnect resume position as `max(lowest_unacked_seq, stored_offset)`, ensuring no unacked event is skipped when ACKs arrive out of order.

## Scope

- Modify `scripts/eventbus/delivery_repo.py`: add `get_resume_position()` function; export it via `__all__` in `scripts/eventbus/db.py` (if applicable).

## Assumptions

- The `consumer_offsets` table has an `offset` column tracking the high-water mark per consumer.
- The `consumer_delivery` table tracks all delivery attempts with `acked_at IS NULL` for unacked events.
- The `events` table has `seq` and `event_id` columns.
- At-least-once delivery (losses not tolerated) is the correct baseline — confirmed by ADR-006.
- Consumers can handle duplicate deliveries — confirmed by the at-least-once baseline.

## Design decisions

- Use `LEFT JOIN` (not `INNER JOIN`) between `events` and `consumer_delivery` so that events with NO `consumer_delivery` record are treated as unacked and will be re-delivered on reconnect.
- Return `0` when no offset exists yet (no prior acks) — the consumer starts from the beginning.
- When no unacked events exist below the stored offset, return `stored_offset + 1` (fast-forward past already-acked events).

## Alternatives considered

- Require consumers to ACK in strict seq order: rejected because it contradicts the at-least-once baseline stated in ADR-006; consumers cannot reliably ACK in strict seq order under network partition or broker reordering.
- Track both low-water mark and high-water mark separately: rejected because it adds schema complexity; the query-based approach derives the low-water mark on demand without persistent state.

## Implementation

### Target file

`scripts/eventbus/delivery_repo.py`

### Procedure

Add `get_resume_position(conn, consumer_id)` function that computes the maximum of the stored offset and the lowest unacked seq among events with seq <= stored offset. Export it via `__all__` in `scripts/eventbus/db.py` if applicable.

### Method

1. In `delivery_repo.py`: add `get_resume_position(conn, consumer_id)` function after `get_consumer_offset()`.
2. In `db.py`: add `get_resume_position` to `__all__` if the module uses it.

### Details

**Change 1 — Add `get_resume_position` function:**

```python
def get_resume_position(conn: sqlite3.Connection, consumer_id: str) -> int:
    """Compute the resume position for a reconnecting consumer.

    Returns the maximum of:
      - The stored offset (high-water mark of acknowledged seq values)
      - The lowest unacked seq among events with seq <= stored offset

    This ensures no unacked event is skipped on reconnect while still
    allowing fast-forward past already-acked events.

    Args:
        conn: SQLite connection.
        consumer_id: Consumer identifier.

    Returns:
        Resume position (int). Returns 0 if no offset exists yet.
    """
    # Get stored offset
    row = conn.execute(
        "SELECT offset FROM consumer_offsets WHERE consumer_id = ?",
        (consumer_id,),
    ).fetchone()
    if row is None:
        return 0  # No offset yet — start from beginning

    stored_offset = int(row["offset"])

    # Find lowest unacked seq <= stored_offset
    # LEFT JOIN required: events with NO consumer_delivery record must be
    # treated as unacked (never attempted for delivery to this consumer).
    row = conn.execute(
        "SELECT MIN(e.seq) FROM events e "
        "LEFT JOIN consumer_delivery cd ON e.event_id = cd.event_id "
        "AND cd.consumer_id = ? "
        "WHERE (cd.acked_at IS NULL OR cd.event_id IS NULL) "
        "AND e.seq <= ?",
        (consumer_id, stored_offset),
    ).fetchone()

    lowest_unacked = int(row[0]) if row and row[0] else stored_offset

    return max(lowest_unacked, stored_offset)
```

**Change 2 — Export in `scripts/eventbus/db.py` (if applicable):**

If `db.py` exports functions from `delivery_repo.py`, add `get_resume_position` to its `__all__`.

## Compatibility considerations

- New public function added to `delivery_repo.py`. Since it is a new addition (not a modification), there is no backward compatibility risk.
- The function is idempotent: calling it multiple times returns the same result unless the database state changes.

## Security considerations

- No security impact. The function reads from existing tables without modifying data.
- The SQL query uses parameterized queries throughout — no injection risk.

## Rollback considerations

- Remove the `get_resume_position` function from `delivery_repo.py`.
- Remove the export from `db.py` if added.
- If `subscribe_route.py` is updated to use this function, revert those changes as well.

## Validation plan

| Target File/Module | Testing Strategy (Unit/Integration) | Tool / Command to Run | Expected Outcome |
|---|---|---|---|
| scripts/eventbus/delivery_repo.py | Static: format, lint, type | `uv run ruff format` / `ruff check` / `uv run mypy` on the file | Clean; no new errors |
| tests/eventbus/test_eventbus_restart_resume.py | Integration (behavior lock + regression) | `uv run pytest tests/eventbus/test_eventbus_restart_resume.py -v` | Passes before and after the edit |
| Full suite | Regression | `uv run pytest tests/` | No new failures |
| Changed lines | Coverage | `uv run diff-cover coverage.xml --compare-branch=master --fail-under=90` | ≥ 90% on changed lines |

## Completion criteria

- [ ] `get_resume_position(conn, consumer_id)` returns `max(lowest_unacked_seq, stored_offset)`.
- [ ] Returns `0` when no offset exists for the consumer.
- [ ] Returns `stored_offset + 1` when all events up to the offset are acked.
- [ ] `ruff format` and `ruff check` pass cleanly on the modified file.
- [ ] `mypy` passes on the modified file.
- [ ] All affected integration tests pass.

## Out of scope

- Changes to `ack_event_for_consumer()` or other delivery repo functions.
- Changes to `subscribe_route.py` (separate procedure document).
- Adding an index on `consumer_delivery(acked_at)` (separate procedure document).
- Documentation updates beyond function docstrings.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | |

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
- **Requirement ID**: REQ-001
- **Source issue**: issues/20261004-095313_eventbus001_eventbus-out-of-order-ack-skips-lower-seq-events-on-resume.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261004-100000_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261005-073241
- **Related target files**: scripts/eventbus/delivery_repo.py
