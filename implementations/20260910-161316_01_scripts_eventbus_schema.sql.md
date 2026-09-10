## Goal

Add per-consumer delivery-state table (`consumer_delivery`) and per-consumer offset table (`consumer_offsets`) DDL to `scripts/eventbus/schema.sql`, replacing the single global `acked_at` column model with a per-consumer delivery-state model.

## Scope

- Add `CREATE TABLE IF NOT EXISTS consumer_delivery` DDL statement after the `events` table definition.
- Add `CREATE TABLE IF NOT EXISTS consumer_offsets` DDL statement after `consumer_delivery`.
- Both tables are additive; no modification to existing `events` table DDL.

## Assumptions

- The new tables follow the same naming convention as the existing `events` table (lowercase, snake_case).
- `consumer_delivery` primary key is `(consumer_id, event_id)` — each consumer can independently ACK the same event.
- `consumer_offsets` primary key is `consumer_id` — one row per consumer tracking its last-committed sequence offset.
- Both tables use SQLite-compatible types: TEXT for identifiers, INTEGER for counts, TEXT for timestamps.

## Design decisions

- Use `INSERT OR IGNORE` semantics for `consumer_delivery` to allow idempotent ACK writes without requiring a prior existence check.
- Use `ON CONFLICT(consumer_id) DO UPDATE SET offset = excluded.offset WHERE excluded.offset > consumer_offsets.offset` for monotonic enforcement — a single atomic SQL statement replaces the current read-then-compare logic.
- Keep `acked_at` on the `events` table for backward compatibility during migration; the new `consumer_delivery` table is the authoritative source going forward.

## Alternatives considered

- **Single normalized table**: Combine delivery state and offset into one `consumer_event_state` table keyed by `(consumer_id, event_id)`. Rejected because offset advancement is a frequent hot-path operation that benefits from a separate index-friendly table.
- **Per-event offset rows**: Store offsets as `(event_id, consumer_id, offset)` tuples. Rejected because the offset is a monotonically advancing counter per consumer, not per event — a single-row-per-consumer design is simpler and faster for the common case.

## Implementation

### Target file

`scripts/eventbus/schema.sql`

### Procedure

Append two new `CREATE TABLE IF NOT EXISTS` statements after the existing `events` table DDL block.

### Method

1. After line 18 (`CREATE INDEX IF NOT EXISTS idx_events_dlq_seq ON events(dlq_at, seq);`), insert the `consumer_delivery` table DDL.
2. After the `consumer_delivery` DDL block, insert the `consumer_offsets` table DDL.
3. No changes to existing lines.

### Details

```sql
-- Per-consumer delivery state: tracks acked_at per (consumer_id, event_id)
CREATE TABLE IF NOT EXISTS consumer_delivery (
    consumer_id          TEXT    NOT NULL,
    event_id             TEXT    NOT NULL,
    acked_at             TEXT,
    PRIMARY KEY (consumer_id, event_id)
);

-- Per-consumer offset: tracks last-committed sequence offset per consumer
CREATE TABLE IF NOT EXISTS consumer_offsets (
    consumer_id          TEXT    PRIMARY KEY,
    offset               INTEGER NOT NULL DEFAULT 0
);
```

- `consumer_delivery`: Primary key `(consumer_id, event_id)` ensures each consumer can independently ACK the same event. `acked_at` is nullable (unset until acknowledged).
- `consumer_offsets`: Primary key `consumer_id` ensures one row per consumer. `offset` defaults to 0 (no events consumed yet). Monotonic enforcement is handled by the SQL statement in `db.py`, not by a trigger or constraint.

## Compatibility considerations

- Existing `events.acked_at` column remains unchanged — this is an additive change only.
- New tables use `CREATE TABLE IF NOT EXISTS` so they are safe to run multiple times.
- The `consumer_delivery` table requires a unique index on `(consumer_id, event_id)` which is provided by the composite primary key.
- The `consumer_offsets` table requires a unique index on `consumer_id` which is provided by the primary key.

## Security considerations

- No new authentication or authorization boundaries introduced.
- Table names and column names follow existing conventions (snake_case, lowercase).
- No user input flows directly into DDL generation — schema changes are code-only.

## Rollback considerations

- To rollback, drop both tables: `DROP TABLE IF EXISTS consumer_offsets; DROP TABLE IF EXISTS consumer_delivery;`
- Dropping order matters: `consumer_offsets` must be dropped before `consumer_delivery` if any foreign-key-like dependency exists (none currently, but future additions may add one).
- The rollback does not restore the old behavior — consumers will lose their committed offsets and delivery state.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/eventbus/schema.sql` | Structural verification | Read file, confirm both new DDL blocks present | Two new `CREATE TABLE IF NOT EXISTS` statements appended after `events` table |
| `tests/db/test_create_schema.py` | Unit test assertion | `uv run pytest tests/db/test_create_schema.py -v` | Test passes, confirms new tables exist in `_EVENTBUS_SCHEMA_NO_VEC0` fixture |

## Completion criteria

- Both `consumer_delivery` and `consumer_offsets` DDL blocks are present in `schema.sql`.
- Both use `CREATE TABLE IF NOT EXISTS` syntax.
- `consumer_delivery` has primary key `(consumer_id, event_id)`.
- `consumer_offsets` has primary key `consumer_id` with `offset INTEGER NOT NULL DEFAULT 0`.
- No existing lines modified.

## Out of scope

- Adding DDL to `scripts/db/schema_sql.py`'s `_EVENTBUS_SCHEMA` string — covered by a separate procedure document.
- Extending `_migrate()` in `scripts/eventbus/db.py` — covered by a separate procedure document.
- Modifying existing `events` table columns or indexes.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add consumer_delivery DDL to schema.sql | Pending | — | — | |
| 2 | Add consumer_offsets DDL to schema.sql | Pending | — | — | |
| 3 | Run validation (pytest + structural check) | Pending | — | — | |

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
- **Source issue**: issues/20260907-125042_eb_h01_transactional_ack_offset_delivery_state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-094115_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-161316
- **Related target files**: scripts/eventbus/schema.sql
