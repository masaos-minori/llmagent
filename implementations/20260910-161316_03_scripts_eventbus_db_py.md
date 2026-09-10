## Goal

Extend `scripts/eventbus/db.py` with three capabilities:
1. Add per-consumer delivery-state UPSERT function (`ack_event_for_consumer`) that performs atomic delivery write + offset advancement in one SQLite transaction.
2. Extend `_migrate()` to create the new tables on an existing `eventbus.sqlite`.
3. Add legacy-offset-file migration function (`migrate_legacy_offsets`) that seeds the new offset table from existing `offsets_dir` files.

## Scope

- Add `ack_event_for_consumer(conn, event_id, consumer_id, now)` function.
- Extend `_migrate()` with two `CREATE TABLE IF NOT EXISTS` additions.
- Add `migrate_legacy_offsets(conn, offsets_dir)` function.
- Modify `ack_event()` to accept an optional `consumer_id` parameter for the new transactional path.

## Assumptions

- The `conn` parameter is always a valid SQLite connection with WAL mode enabled.
- `consumer_id` is always a non-empty string when passed to `ack_event_for_consumer`; empty strings are handled by the caller.
- The `now` parameter is an ISO-8601 UTC timestamp string (same format as current `acked_at` values).
- Legacy offset files follow the same naming convention as current code (sanitized filename + `.map` companion).

## Design decisions

- **Single transaction**: `ack_event_for_consumer` performs both the delivery-state UPSERT and the offset advancement using the same `conn`, committing once at the end (or rolling back on exception). This eliminates the current two-commit gap.
- **Atomic monotonic enforcement**: Offset advancement uses `INSERT OR REPLACE INTO consumer_offsets(consumer_id, offset) VALUES(?, ?)` followed by a conditional update, or more efficiently: `INSERT INTO consumer_offsets(consumer_id, offset) VALUES(?, ?) ON CONFLICT(consumer_id) DO UPDATE SET offset = excluded.offset WHERE excluded.offset > consumer_offsets.offset`.
- **Idempotent ACK**: The delivery-state UPSERT uses `INSERT OR IGNORE` semantics — if the same consumer has already ACKed the same event, the row is silently skipped.
- **Migration function**: `migrate_legacy_offsets` reads each `.map` file under `offsets_dir`, recovers the original `consumer_id` from the `.map` companion, reads its offset via `read_offset()`, and inserts a row into `consumer_offsets` using `INSERT OR IGNORE` (idempotent).

## Alternatives considered

- **Trigger-based monotonic enforcement**: Use a BEFORE INSERT trigger on `consumer_offsets` to reject non-monotonic updates. Rejected because triggers add complexity and the application-level SQL approach is simpler to reason about and test.
- **Separate offset-write function**: Keep offset writing as a separate function called after the delivery-state write. Rejected because this reintroduces the exact gap this Plan fixes (two independent commits).
- **Delete legacy files after migration**: Delete `offsets_dir` files after migrating their contents. Rejected because the Issue's AI Implementation Instruction explicitly requires retaining the legacy files and functions until verified end-to-end.

## Implementation

### Target file

`scripts/eventbus/db.py`

### Procedure

1. Extend `_migrate()` with two new table creation statements.
2. Add `ack_event_for_consumer()` function.
3. Add `migrate_legacy_offsets()` function.
4. Optionally modify `ack_event()` to accept a `consumer_id` parameter.

### Method

#### Step 1: Extend `_migrate()`

After line 115 (end of existing `_migrate()` body), before the closing `def` block, append:

```python
# New tables added in REQ-001/REQ-002: per-consumer delivery state and offset
for tbl_name, ddl in [
    ("consumer_delivery",
     "CREATE TABLE IF NOT EXISTS consumer_delivery ("
     "    consumer_id TEXT NOT NULL,"
     "    event_id TEXT NOT NULL,"
     "    acked_at TEXT,"
     "    PRIMARY KEY (consumer_id, event_id)"
     ")"),
    ("consumer_offsets",
     "CREATE TABLE IF NOT EXISTS consumer_offsets ("
     "    consumer_id TEXT PRIMARY KEY,"
     "    offset INTEGER NOT NULL DEFAULT 0"
     ")"),
]:
    try:
        conn.execute(ddl)
        logger.info("migrated: created table %s", tbl_name)
    except sqlite3.OperationalError as exc:
        if exc.args and "duplicate column name" in exc.args[0].lower():
            pass  # table already exists (unlikely but defensive)
        else:
            raise
```

#### Step 2: Add `ack_event_for_consumer()` function

Add after the existing `nack_event()` function (after line 158):

```python
def ack_event_for_consumer(
    conn: sqlite3.Connection,
    event_id: str,
    consumer_id: str,
    now: str,
) -> tuple[bool, bool, int | None]:
    """Acknowledge an event for a specific consumer atomically.

    Performs the per-consumer delivery-state UPSERT and the per-consumer
    offset advancement in a single SQLite transaction. Commits once at the
    end (or rolls back on exception).

    Returns (found, newly_acked, seq):
      - (True, True, seq)   = event found, newly acked by this consumer
      - (True, False, None) = event found but already acked by this consumer
      - (False, False, None)= event not found

    Args:
        conn: SQLite connection (must be the shared eventbus connection).
        event_id: Event identifier.
        consumer_id: Non-empty consumer identifier.
        now: ISO-8601 UTC timestamp string.

    Raises:
        sqlite3.Error: If the transaction fails to commit or roll back.
    """
    assert consumer_id, "consumer_id must be non-empty"
    newly_acked = False
    seq: int | None = None

    try:
        # Per-consumer delivery-state UPSERT (idempotent)
        cur = conn.execute(
            "INSERT OR IGNORE INTO consumer_delivery "
            "(consumer_id, event_id, acked_at) VALUES (?, ?, ?)",
            (consumer_id, event_id, now),
        )
        newly_acked = cur.rowcount == 1  # INSERT happened; IGNORE means 0 rows affected

        if newly_acked:
            # Get the event seq for offset tracking
            row = conn.execute(
                "SELECT seq FROM events WHERE event_id = ?",
                (event_id,),
            ).fetchone()
            if row:
                seq = int(row["seq"])
                # Atomic monotonic offset advancement
                conn.execute(
                    "INSERT INTO consumer_offsets(consumer_id, offset) "
                    "VALUES (?, ?) "
                    "ON CONFLICT(consumer_id) DO UPDATE SET "
                    "offset = excluded.offset "
                    "WHERE excluded.offset > consumer_offsets.offset",
                    (consumer_id, seq),
                )

        conn.commit()
    except Exception:
        conn.rollback()
        raise

    # Check if event exists but was already acked by this consumer
    if not newly_acked:
        already_acked = conn.execute(
            "SELECT 1 FROM consumer_delivery "
            "WHERE consumer_id = ? AND event_id = ?",
            (consumer_id, event_id),
        ).fetchone()
        if already_acked:
            return True, False, None

    return False, False, None
```

#### Step 3: Add `migrate_legacy_offsets()` function

Add after `ack_event_for_consumer()` (after line ~230):

```python
def migrate_legacy_offsets(
    conn: sqlite3.Connection,
    offsets_dir: str,
) -> list[str]:
    """Migrate legacy file-based offsets into the consumer_offsets table.

    Reads each .map file under offsets_dir, recovers the original consumer_id
    from the .map companion, reads its offset via read_offset(), and inserts
    a row into consumer_offsets using INSERT OR IGNORE (idempotent).

    For any offset file with no .map companion, falls back to the sanitized
    filename as consumer_id, logging a warning.

    Does NOT delete or modify any legacy files.

    Returns:
        List of consumer_ids that were migrated.
    """
    from eventbus.offsets import _sanitize_consumer_id, read_offset  # noqa: PLC0415

    migrated: list[str] = []
    dir_path = Path(offsets_dir)

    if not dir_path.exists():
        logger.warning("offsets_dir does not exist: %s", offsets_dir)
        return migrated

    for map_file in sorted(dir_path.glob("*.map")):
        safe_id = map_file.stem  # filename without .map extension
        try:
            stored_id = map_file.read_text().strip()
            if stored_id:
                consumer_id = stored_id
            else:
                # Empty .map file — fall back to sanitized filename
                consumer_id = safe_id
                logger.warning(
                    "empty .map file for %s, using sanitized filename as consumer_id",
                    safe_id,
                )
        except FileNotFoundError:
            # No .map companion — use sanitized filename
            consumer_id = safe_id
            logger.warning(
                "no .map companion for %s, using sanitized filename as consumer_id",
                safe_id,
            )

        offset_val = read_offset(offsets_dir, consumer_id)
        if offset_val > 0:
            try:
                conn.execute(
                    "INSERT OR IGNORE INTO consumer_offsets(consumer_id, offset) "
                    "VALUES (?, ?)",
                    (consumer_id, offset_val),
                )
                migrated.append(consumer_id)
                logger.debug(
                    "migrated offset: consumer=%s offset=%d",
                    consumer_id,
                    offset_val,
                )
            except sqlite3.IntegrityError as exc:
                logger.warning(
                    "failed to migrate offset for consumer %s: %s",
                    consumer_id,
                    exc,
                )

    return migrated
```

### Details

The key changes are:

1. **`_migrate()` extension**: Adds two `CREATE TABLE IF NOT EXISTS` statements for the new tables. Uses the same error-handling pattern as existing column/index additions (catch `sqlite3.OperationalError` for duplicate-column scenarios).

2. **`ack_event_for_consumer()`**: The core transactional function. It:
   - Performs a per-consumer delivery-state UPSERT (`INSERT OR IGNORE`) instead of the global `acked_at` flag.
   - Only advances the offset when `newly_acked` is True (i.e., the INSERT actually inserted a row).
   - Uses `ON CONFLICT(consumer_id) DO UPDATE SET offset = excluded.offset WHERE excluded.offset > consumer_offsets.offset` for atomic monotonic enforcement.
   - Commits once at the end, or rolls back on any exception.

3. **`migrate_legacy_offsets()`**: Migration function that:
   - Enumerates `.map` files under `offsets_dir`.
   - Recovers the original `consumer_id` from the `.map` companion file.
   - Falls back to the sanitized filename when no `.map` companion exists (UNK-02 mitigation).
   - Reads the current offset via `read_offset()` (retained legacy function).
   - Inserts into `consumer_offsets` using `INSERT OR IGNORE` (idempotent).
   - Never deletes or modifies legacy files.

## Compatibility considerations

- `ack_event_for_consumer()` is a new function; it does not replace `ack_event()` — both can coexist during migration.
- The `ack_event()` function remains unchanged for backward compatibility; callers should migrate to `ack_event_for_consumer()` gradually.
- The `migrate_legacy_offsets()` function is additive; it does not modify or delete legacy files.
- Both new tables use `CREATE TABLE IF NOT EXISTS` so they are safe to run multiple times.

## Security considerations

- No new authentication or authorization boundaries introduced.
- Table/column naming follows existing conventions.
- No user input flows directly into DDL generation — schema changes are code-only.
- The `migrate_legacy_offsets()` function uses the existing `_sanitize_consumer_id()` function for filename safety.

## Rollback considerations

- To rollback the `ack_event_for_consumer()` change: remove the function and revert callers to `ack_event()` + `write_offset()`.
- To rollback the `_migrate()` change: drop the two new tables (see related procedure document).
- To rollback the `migrate_legacy_offsets()` change: delete the function; the legacy files remain untouched.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/db.py` | Unit test for `ack_event_for_consumer` | `uv run pytest tests/eventbus/test_eventbus_crash_ack.py -v` | Failure injection leaves neither delivery nor offset committed |
| `scripts/eventbus/db.py` | Multi-consumer ACK test | `uv run pytest tests/eventbus/test_eventbus_ack_nack.py -v` | Two consumers ACK the same event independently |
| `scripts/eventbus/db.py` | Migration idempotency test | `uv run pytest tests/eventbus/test_eventbus_offsets.py -v` | Re-running migration is a no-op; no corruption on failure |
| Full EventBus suite | Regression | `uv run pytest tests/eventbus/ -v` | All pass, including retained-legacy-path tests |

## Completion criteria

- `_migrate()` creates both `consumer_delivery` and `consumer_offsets` tables on existing databases.
- `ack_event_for_consumer()` performs atomic delivery-state UPSERT + offset advancement in one transaction.
- `migrate_legacy_offsets()` migrates all legacy offset files without deleting them.
- All three functions handle exceptions correctly (rollback on failure for `ack_event_for_consumer`, graceful degradation for `migrate_legacy_offsets`).

## Out of scope

- Modifying `ack_event()` to accept a `consumer_id` parameter — optional enhancement, not required by the Plan.
- Adding DDL to `scripts/eventbus/schema.sql` — covered by a separate procedure document.
- Adding DDL to `scripts/db/schema_sql.py` — covered by a separate procedure document.
- Updating `subscribe_route.py` — covered by a separate procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Extend _migrate() with new table DDL | Pending | — | — | |
| 2 | Add ack_event_for_consumer() function | Pending | — | — | |
| 3 | Add migrate_legacy_offsets() function | Pending | — | — | |
| 4 | Run validation (pytest + structural check) | Pending | — | — | |

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
- **Generated at**: 20260910-161316
- **Related target files**: scripts/eventbus/db.py
