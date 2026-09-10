## Goal
Add the DDL for two new per-consumer tables — a delivery-state table and an offset
table — to `scripts/eventbus/schema.sql`, the DDL source read by
`scripts/eventbus/db.py::_init_schema()` when bootstrapping a brand-new
`eventbus.sqlite` (REQ-001, REQ-002; purpose: let independent consumers each track
their own ACK/offset state).

## Scope
In scope: adding two `CREATE TABLE IF NOT EXISTS` statements (and any supporting
index) to this file only. Out of scope: any change to the existing `events` table or
its indexes; any change to `scripts/db/schema_sql.py` (row 02, seq `20260910-092106_02`)
or `scripts/eventbus/db.py::_migrate()` (row 03, seq `20260910-092106_03`) — those are
separate target-file rows.

## Assumptions
- SQLite supports `CREATE TABLE IF NOT EXISTS`, matching the existing idempotent style
  already used for `events` and its indexes in this same file.
- `consumer_id` is an application-level string with no separate consumers table to
  foreign-key against — matches the existing `events` table, which also has no foreign
  keys.

## Design decisions
- New table `consumer_delivery`: primary key `(consumer_id, event_id)`, one nullable
  `acked_at TEXT` column — the per-consumer analogue of `events.acked_at`, but scoped to
  a consumer instead of global.
- New table `consumer_offsets`: primary key `consumer_id`, one `seq INTEGER NOT NULL`
  column holding the last-committed offset — replaces `offsets_dir` files as the
  live-service store (REQ-002).
- Both tables are additive `CREATE TABLE IF NOT EXISTS` statements, following the exact
  style already used for `events` in this file — no change to existing DDL.

## Alternatives considered
- A single combined table keyed by `(consumer_id, event_id)` carrying both delivery
  state and a running per-consumer offset was considered and rejected: offset
  advancement is a per-`consumer_id` operation independent of any specific `event_id`,
  so combining the two would require a sentinel row or duplicate offset values across
  every delivery row for that consumer.

## Implementation
### Target file
`scripts/eventbus/schema.sql`

### Procedure
1. Append the two new `CREATE TABLE IF NOT EXISTS` statements after the existing
   `events` table block and its indexes, preserving the file's existing statement
   order (table, then indexes).
2. Add an index on `consumer_delivery(consumer_id)` if lookups by consumer alone are
   needed by `scripts/eventbus/db.py`'s new query functions (row 03) — confirm during
   that row's implementation whether the primary key alone is sufficient, since SQLite
   already indexes the leading column of a composite primary key.

### Method
Direct text edit — append DDL blocks; no procedural logic in this file.

### Details
```sql
CREATE TABLE IF NOT EXISTS consumer_delivery (
    consumer_id TEXT NOT NULL,
    event_id    TEXT NOT NULL,
    acked_at    TEXT,
    PRIMARY KEY (consumer_id, event_id)
);

CREATE TABLE IF NOT EXISTS consumer_offsets (
    consumer_id TEXT PRIMARY KEY,
    seq         INTEGER NOT NULL
);
```
Column names/types must match exactly what `scripts/db/schema_sql.py`'s
`_EVENTBUS_SCHEMA` (row 02) and `scripts/eventbus/db.py::_migrate()` (row 03) use — the
three sources must define identical tables (AC-7).

## Compatibility considerations
Purely additive: no existing column, table, or index in this file is changed or
removed. `_init_schema()` only runs this file's DDL against a brand-new database file,
so no live data migration is involved here — the live-upgrade path for an existing
`eventbus.sqlite` is `_migrate()` (row 03), not this file.

## Security considerations
No new user input reaches this DDL directly; `consumer_id` values are always bound via
parameterized queries in the functions that read/write these tables (row 03), never
interpolated into SQL text.

## Rollback considerations
Revert this file's diff (`git checkout` on this file, or revert the commit). Since the
tables are never populated until row 03's new functions exist, an unused `CREATE TABLE
IF NOT EXISTS` left in place after a partial rollback is harmless — dropping the tables
explicitly is not required for rollback safety.

## Validation plan
- `uv run pytest tests/db/test_create_schema.py -v` (indirectly, via the migration
  path exercised through `scripts/eventbus/db.py::_init_schema()` — this file's own
  bootstrap path).
- `uv run pytest tests/eventbus/test_eventbus_offsets.py -v` once row 03/07's functions
  exist and depend on these tables.
- Manual: `sqlite3 :memory: < scripts/eventbus/schema.sql` (or equivalent) to confirm
  the file parses with no syntax error before relying on any downstream test.

## Completion criteria
Both `CREATE TABLE IF NOT EXISTS` statements are present in
`scripts/eventbus/schema.sql`, syntactically valid, and structurally identical (column
names, types, primary key) to the corresponding DDL added to
`scripts/db/schema_sql.py`'s `_EVENTBUS_SCHEMA` (row 02).

## Out of scope
Any change to `scripts/eventbus/db.py` (`_migrate()`, new query functions) — row 03.
Any change to `scripts/db/schema_sql.py` — row 02. Any change to `events` table
columns (`delivery_failure_count`, `dlq_at` stay global per Plan Out-of-Scope).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Add `consumer_delivery` and `consumer_offsets` `CREATE TABLE IF NOT EXISTS` DDL | Pending | — | — | |
| 2 | Confirm DDL matches `scripts/db/schema_sql.py`'s `_EVENTBUS_SCHEMA` (row 02) | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | N/A: no documentation update in this file's own scope (see Documentation Impact rows 12-14) | Pending | — | — | |

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
- **Requirement ID**: REQ-001, REQ-002 (add per-consumer delivery-state and offset tables)
- **Source issue**: issues/20260907-125042_eb_h01_transactional_ack_offset_delivery_state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-094115_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-092106
- **Related target files**: scripts/eventbus/schema.sql
