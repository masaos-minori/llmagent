## Goal
Extend `scripts/eventbus/db.py` with: (1) `_migrate()` additions so an existing
`eventbus.sqlite` picks up the two new tables on next startup (REQ-001, REQ-002); (2)
one new function performing the per-consumer delivery write and offset advancement in
a single transaction (REQ-001, REQ-002, REQ-003); (3) one new function migrating
legacy `offsets_dir` files into the new offset table (REQ-004).

## Scope
In scope: `_migrate()` extension; a new `ack_event_for_consumer(conn, event_id,
consumer_id, now)` function; a new `migrate_legacy_offsets(conn, offsets_dir)`
function; a new read function for `subscribe_route.py`'s offset lookup (row 05). Out
of scope: `ack_route.py`'s call-site change (row 04), `subscribe_route.py`'s read-path
switch (row 05), `app.py`'s wiring of the migration call (row 06) — those are separate
target-file rows. `nack_event()`, `dlq`-related columns (`delivery_failure_count`,
`dlq_at`) are untouched (global, per Plan Out-of-Scope).

## Assumptions
- The existing `_db_lock`/`run_with_db_lock()` serialization (confirmed via
  `scripts/eventbus/route_helpers.py::run_with_db_lock()`) already prevents
  concurrent-request interleaving within one process; the new function's
  single-transaction design is a correctness-independent-of-locking improvement, not a
  fix for an actively-reproducing concurrency bug.
- `offsets.py`'s `read_offset()`/`_sanitize_consumer_id()` remain unmodified and are
  reused as-is by `migrate_legacy_offsets()` (confirmed: `offsets.py` is a Reference
  File in the Plan, not a target file).

## Design decisions
- **`ack_event_for_consumer(conn, event_id, consumer_id, now)`**: performs an `INSERT
  INTO consumer_delivery (...) ON CONFLICT (consumer_id, event_id) DO NOTHING`-style
  UPSERT (idempotent, matching `ack_event()`'s existing "will not overwrite existing
  ack" semantics), then — only when the delivery row was newly inserted — advances
  `consumer_offsets` via a single conditional statement, then commits once. On any
  exception between the two writes, `conn.rollback()` is called explicitly before
  re-raising, so the delivery write and the offset write always land together or not
  at all (REQ-003).
- **Atomic monotonic enforcement**: offset advancement uses
  `INSERT INTO consumer_offsets (consumer_id, seq) VALUES (?, ?)
  ON CONFLICT(consumer_id) DO UPDATE SET seq = excluded.seq
  WHERE excluded.seq > consumer_offsets.seq` (or an equivalent `UPDATE ... WHERE seq <
  ?` checked via `cur.rowcount`) — a single SQL statement, not `write_offset()`'s
  current read-then-compare (REQ-002, per the Issue's explicit requirement).
- **`migrate_legacy_offsets(conn, offsets_dir)`**: enumerates `.map` files under
  `offsets_dir` (reusing `offsets.py`'s existing sanitization/read pattern), reads each
  real `consumer_id` via the `.map` file's stored value and its offset via
  `read_offset()`, and `INSERT OR IGNORE`s a row per consumer into `consumer_offsets` —
  idempotent (`OR IGNORE` skips already-migrated consumers) and additive (never
  touches or deletes legacy files). Falls back to the sanitized filename as
  `consumer_id` when no `.map` companion exists for an offset file (UNK-02), logging a
  warning in that case.
- `_migrate()` gets the same `CREATE TABLE IF NOT EXISTS` additions as row 01/02,
  following the existing idempotent-migration pattern already used for column/index
  additions in this function.

## Alternatives considered
Performing the offset advancement via a Python-level read-then-conditional-write (`SELECT`
then `UPDATE` only if newer) was considered and rejected: this reproduces
`write_offset()`'s current race-prone read-then-compare pattern that REQ-002
explicitly requires replacing with a single atomic SQL statement.

## Implementation
### Target file
`scripts/eventbus/db.py`

### Procedure
1. In `_migrate()`, add `CREATE TABLE IF NOT EXISTS` statements for
   `consumer_delivery` and `consumer_offsets`, following the same
   try/`OperationalError`-tolerant style already used for the column/index additions
   in this function (though `CREATE TABLE IF NOT EXISTS` itself does not raise on
   re-run, so no exception handling is needed for these two statements specifically).
2. Add `ack_event_for_consumer(conn, event_id, consumer_id, now)`: run the
   `consumer_delivery` UPSERT; if it inserted a new row (check `cur.rowcount` or an
   equivalent post-insert existence check), run the `consumer_offsets` atomic
   advancement using the event's `seq` (looked up via the existing `SELECT seq FROM
   events WHERE event_id = ?` pattern already used in `ack_route.py`); commit once at
   the end; wrap in try/except to `conn.rollback()` and re-raise on any exception
   before the final commit.
3. Add `migrate_legacy_offsets(conn, offsets_dir)`: iterate `.map` files, resolve each
   `consumer_id`/offset pair via `offsets.read_offset()`, `INSERT OR IGNORE` into
   `consumer_offsets`. No transaction rollback complexity needed here since
   `INSERT OR IGNORE` is naturally idempotent per-row; commit once after the loop.
4. Add a small read helper (e.g. `get_consumer_offset(conn, consumer_id) -> int`) for
   `subscribe_route.py` (row 05) to read the new table — returns `0` when no row
   exists, matching `read_offset()`'s current default-to-zero behavior.

### Method
New functions added following the module's existing style: plain functions taking
`conn: sqlite3.Connection` as the first argument, no class wrapping, consistent with
`ack_event()`/`nack_event()`/`insert_event()` already in this file.

### Details
```python
def ack_event_for_consumer(
    conn: sqlite3.Connection, event_id: str, consumer_id: str, now: str
) -> tuple[bool, bool]:
    """Ack an event for one consumer and advance its offset, in one transaction.

    Returns (found, newly_acked) matching ack_event()'s existing contract.
    """
    try:
        row = conn.execute(
            "SELECT seq FROM events WHERE event_id = ?", (event_id,)
        ).fetchone()
        if row is None:
            return False, False
        seq = int(row["seq"])
        cur = conn.execute(
            "INSERT INTO consumer_delivery (consumer_id, event_id, acked_at) "
            "VALUES (?, ?, ?) "
            "ON CONFLICT (consumer_id, event_id) DO NOTHING",
            (consumer_id, event_id, now),
        )
        newly_acked = cur.rowcount > 0
        if newly_acked:
            conn.execute(
                "INSERT INTO consumer_offsets (consumer_id, seq) VALUES (?, ?) "
                "ON CONFLICT(consumer_id) DO UPDATE SET seq = excluded.seq "
                "WHERE excluded.seq > consumer_offsets.seq",
                (consumer_id, seq),
            )
        conn.commit()
        return True, newly_acked
    except Exception:
        conn.rollback()
        raise


def migrate_legacy_offsets(conn: sqlite3.Connection, offsets_dir: str) -> int:
    """Seed consumer_offsets from legacy offsets_dir .map files. Idempotent."""
    from eventbus.offsets import read_offset  # noqa: PLC0415

    migrated = 0
    offsets_path = Path(offsets_dir)
    if not offsets_path.is_dir():
        return 0
    for map_file in offsets_path.glob("*.map"):
        stored_id = map_file.read_text().strip()
        consumer_id = stored_id or map_file.stem  # UNK-02 fallback
        seq = read_offset(offsets_dir, consumer_id)
        cur = conn.execute(
            "INSERT OR IGNORE INTO consumer_offsets (consumer_id, seq) VALUES (?, ?)",
            (consumer_id, seq),
        )
        migrated += cur.rowcount
    conn.commit()
    return migrated


def get_consumer_offset(conn: sqlite3.Connection, consumer_id: str) -> int:
    """Read a consumer's last-committed offset from consumer_offsets. Defaults to 0."""
    row = conn.execute(
        "SELECT seq FROM consumer_offsets WHERE consumer_id = ?", (consumer_id,)
    ).fetchone()
    return int(row["seq"]) if row else 0
```
`Path` must be imported at module scope (`from pathlib import Path`) if not already
present — verify before adding to avoid a duplicate import.

## Compatibility considerations
`_migrate()`'s additions are purely additive and idempotent — an existing
`eventbus.sqlite` gains the two tables on next startup with no data loss.
`ack_event_for_consumer()` and `migrate_legacy_offsets()` are new functions;
`ack_event()`/`write_offset()` remain unmodified and still work for any caller not yet
switched to the new path (only `ack_route.py`, row 04, switches).

## Security considerations
`consumer_id` and `event_id` are always bound via parameterized queries (`?`
placeholders) — never interpolated into SQL text, consistent with every existing
query in this file.

## Rollback considerations
Revert this file's diff. Since `ack_route.py` (row 04) is the only caller of
`ack_event_for_consumer()`, reverting both files together restores the prior
two-call, two-commit behavior with no schema rollback needed (the new tables remain
unused but harmless if only this file is reverted alone).

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_ack_nack.py -v` (row 08): two distinct
  `consumer_id`s ACK the same event independently (AC-1, AC-2).
- `uv run pytest tests/eventbus/test_eventbus_crash_ack.py -v` (row 09): failure
  injected into the offset-advancement step after the delivery-state write; assert
  rollback leaves neither committed (AC-3).
- `uv run pytest tests/eventbus/test_eventbus_offsets.py -v` (row 07): monotonic
  enforcement (AC-4) and migration idempotency (AC-5), including a legacy file with no
  `.map` companion.

## Completion criteria
`ack_event_for_consumer()` commits both writes together or rolls back both on
failure (verified by a forced-failure test); `consumer_offsets` advancement never
regresses on an older-or-equal `seq`; `migrate_legacy_offsets()` is a no-op on a second
invocation against the same `offsets_dir`; `_migrate()` adds both new tables to an
existing database file without error.

## Out of scope
Any change to `ack_event()`, `nack_event()`, or any `dlq`-related column/function in
this file — these remain global (event-level), per Plan Out-of-Scope and UNK-01's
conservative resolution.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend `_migrate()` with the two new `CREATE TABLE IF NOT EXISTS` statements | Pending | — | — | |
| 2 | Add `ack_event_for_consumer()` with single-transaction commit/rollback | Pending | — | — | |
| 3 | Add `migrate_legacy_offsets()` with the no-`.map`-companion fallback | Pending | — | — | |
| 4 | Add `get_consumer_offset()` read helper for row 05 | Pending | — | — | |
| 5 | Add or update tests per Validation plan (rows 07-09) | Pending | — | — | |
| 6 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002, REQ-003, REQ-004
- **Source issue**: issues/20260907-125042_eb_h01_transactional_ack_offset_delivery_state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-094115_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-092106
- **Related target files**: scripts/eventbus/db.py
