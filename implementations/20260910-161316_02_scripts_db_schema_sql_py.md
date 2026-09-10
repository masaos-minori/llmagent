## Goal

Add matching per-consumer delivery-state table (`consumer_delivery`) and per-consumer offset table (`consumer_offsets`) DDL to `scripts/db/schema_sql.py`'s `_EVENTBUS_SCHEMA` string, keeping it consistent with `scripts/eventbus/schema.sql`.

## Scope

- Append two new `CREATE TABLE IF NOT EXISTS` statements to the `_EVENTBUS_SCHEMA` string literal.
- Both tables match the definitions added to `scripts/eventbus/schema.sql` (see related procedure document).

## Assumptions

- The `_EVENTBUS_SCHEMA` string follows the same format as the existing `events` table DDL within it.
- The two DDL sources (`schema.sql` and `_EVENTBUS_SCHEMA`) must remain identical for the new tables to avoid divergence between bootstrap and live-service paths.

## Design decisions

- Mirror the exact DDL from `scripts/eventbus/schema.sql` to ensure consistency across both initialization paths.
- Use `CREATE TABLE IF NOT EXISTS` for idempotent bootstrapping.

## Alternatives considered

- **Centralized DDL module**: Extract shared DDL into a separate module imported by both `schema.sql` reader and `build_eventbus_schema_sql()`. Rejected because `schema.sql` is a static file, not a Python module, and the two initialization paths have different loading mechanisms.

## Implementation

### Target file

`scripts/db/schema_sql.py`

### Procedure

Append two new `CREATE TABLE IF NOT EXISTS` statements after the existing `events` table DDL block within the `_EVENTBUS_SCHEMA` string.

### Method

1. Locate the end of the `_EVENTBUS_SCHEMA` string (after line 251: `CREATE INDEX IF NOT EXISTS idx_events_dlq_seq ON events(dlq_at, seq);`).
2. Insert the `consumer_delivery` table DDL.
3. Insert the `consumer_offsets` table DDL.
4. Close the triple-quote string delimiter.

### Details

After line 251 (`CREATE INDEX IF NOT EXISTS idx_events_dlq_seq ON events(dlq_at, seq);`), before the closing `"""`, append:

```python
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

The updated `_EVENTBUS_SCHEMA` string should look like:

```python
_EVENTBUS_SCHEMA: str = """
PRAGMA journal_mode=WAL;

-- Timestamps use ISO-8601 UTC Z suffix format: 2026-07-02T10:00:00Z
-- acked_at and dlq_at are nullable (unset until acknowledged/dead-lettered)

CREATE TABLE IF NOT EXISTS events (
    ...existing events table DDL...
);

CREATE INDEX IF NOT EXISTS idx_events_topic ON events(topic);
CREATE INDEX IF NOT EXISTS idx_events_seq   ON events(seq);
CREATE INDEX IF NOT EXISTS idx_events_dlq_at ON events(dlq_at);
CREATE INDEX IF NOT EXISTS idx_events_dlq_seq ON events(dlq_at, seq);

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
"""
```

## Compatibility considerations

- The `_EVENTBUS_SCHEMA` string must remain valid SQL when passed to `sqlite3.connect().executescript()`.
- Both new tables use `CREATE TABLE IF NOT EXISTS` so they are safe to run during bootstrap even if the database already exists.
- The `consumer_delivery` table's composite primary key provides an implicit unique index on `(consumer_id, event_id)`.
- The `consumer_offsets` table's primary key provides an implicit unique index on `consumer_id`.

## Security considerations

- No new authentication or authorization boundaries introduced.
- Table/column naming follows existing conventions.
- No user input flows into DDL generation.

## Rollback considerations

- To rollback, remove the two `CREATE TABLE IF NOT EXISTS` blocks from the string.
- The rollback restores the pre-change state where both DDL sources are consistent again.

## Validation plan

| Target | Testing Strategy | Tool / Command | Expected Outcome |
|---|---|---|---|
| `scripts/db/schema_sql.py` | Structural verification | Read file, confirm both new DDL blocks present in `_EVENTBUS_SCHEMA` | Two new `CREATE TABLE IF NOT EXISTS` statements appended after `events` table |
| `tests/db/test_create_schema.py` | Unit test assertion | `uv run pytest tests/db/test_create_schema.py -v` | Test passes, confirms new tables exist in `_EVENTBUS_SCHEMA_NO_VEC0` fixture |

## Completion criteria

- Both `consumer_delivery` and `consumer_offsets` DDL blocks are present in `_EVENTBUS_SCHEMA`.
- Both use `CREATE TABLE IF NOT EXISTS` syntax.
- DDL matches `scripts/eventbus/schema.sql` definitions exactly.
- No existing lines modified except appending new content.

## Out of scope

- Adding DDL to `scripts/eventbus/schema.sql` — covered by a separate procedure document.
- Extending `_migrate()` in `scripts/eventbus/db.py` — covered by a separate procedure document.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add consumer_delivery DDL to _EVENTBUS_SCHEMA | Pending | — | — | |
| 2 | Add consumer_offsets DDL to _EVENTBUS_SCHEMA | Pending | — | — | |
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
- **Related target files**: scripts/db/schema_sql.py
