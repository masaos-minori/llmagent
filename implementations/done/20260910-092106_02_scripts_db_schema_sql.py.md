## Goal
Add the identical `consumer_delivery`/`consumer_offsets` DDL to
`scripts/db/schema_sql.py`'s `_EVENTBUS_SCHEMA` string, the second, independent DDL
source used by `db/create_schema.py::create_eventbus_schema()`'s bootstrap path
(REQ-001, REQ-002), so a freshly bootstrapped `eventbus.sqlite` and a live-service
upgraded one produce the same table set (AC-7).

## Scope
In scope: editing the `_EVENTBUS_SCHEMA` string literal only (returned unchanged by
`build_eventbus_schema_sql()`). Out of scope: any change to `scripts/eventbus/schema.sql`
(row 01) or `scripts/eventbus/db.py::_migrate()` (row 03) — this row's only job is
keeping this second DDL source in sync with those.

## Assumptions
- `_EVENTBUS_SCHEMA` is a plain triple-quoted string executed wholesale by
  `create_eventbus_schema()`; no templating or per-table function boundary exists to
  preserve — appending text is sufficient.
- This file also defines rag/session/workflow schema strings, unrelated and untouched.

## Design decisions
Add the same two `CREATE TABLE IF NOT EXISTS` statements as row 01
(`scripts/eventbus/schema.sql`), verbatim in column name/type/primary-key structure —
this row exists solely to prevent the two-DDL-source drift risk documented in the
Plan's `docs/90_shared_04_03_db_architecture_and_schema-migration-and-scaling.md`
section 8b (row 14) and Risks.

## Alternatives considered
Deriving `_EVENTBUS_SCHEMA` from `scripts/eventbus/schema.sql` at runtime (read the
file instead of duplicating the string) was considered and rejected: it would change
`create_eventbus_schema()`'s existing self-contained-string behavior for all four
schema kinds (rag/session/workflow/eventbus) it defines, which is out of scope for
this Plan (REQ-001/REQ-002 only add tables, they do not restructure the module).

## Implementation
### Target file
`scripts/db/schema_sql.py`

### Procedure
1. Append the two `CREATE TABLE IF NOT EXISTS` statements to the end of the
   `_EVENTBUS_SCHEMA` string (inside the triple-quoted literal, before the closing
   `"""`), after the existing `events` table's indexes.
2. Do not alter `build_eventbus_schema_sql()` itself — it already returns
   `_EVENTBUS_SCHEMA` unchanged and needs no logic change.

### Method
Direct text edit inside the string literal; no procedural logic change.

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
This must be byte-for-byte structurally identical (columns, types, primary key) to row
01's DDL — divergence here is exactly the drift risk this row exists to close.

## Compatibility considerations
Additive only; the three other schema strings in this file (rag/session/workflow) are
untouched. `create_eventbus_schema()`'s existing `CREATE TABLE IF NOT EXISTS`-only,
always-idempotent bootstrap pattern (confirmed via `scripts/db/create_schema.py`)
means no `ALTER TABLE`-style migration logic is needed on this path for these two
brand-new tables.

## Security considerations
No new input path; the string is static DDL with no interpolation.

## Rollback considerations
Revert this file's diff. No data exists in these tables via this bootstrap path until
`create_eventbus_schema()` is invoked against a real target, so reverting is a clean,
no-data-loss operation.

## Validation plan
- `uv run pytest tests/db/test_create_schema.py -v` — specifically the new assertion
  added in row 11 confirming `create_eventbus_schema()` produces the new tables
  (AC-7).
- Manual diff-comparison against row 01's DDL text to confirm structural identity
  before considering this row done.

## Completion criteria
`_EVENTBUS_SCHEMA` contains both new `CREATE TABLE IF NOT EXISTS` statements,
structurally identical to `scripts/eventbus/schema.sql` (row 01), and
`create_eventbus_schema()` continues to return successfully with no behavior change to
the rag/session/workflow schema strings.

## Out of scope
Any change to `build_eventbus_schema_sql()`'s signature or the rag/session/workflow
schema strings in this same file.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Append matching `consumer_delivery`/`consumer_offsets` DDL to `_EVENTBUS_SCHEMA` | Completed | — | — | |
| 2 | Diff-confirm structural identity with row 01 (`scripts/eventbus/schema.sql`) | Completed | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | — | — | |
| 4 | N/A: no documentation update in this file's own scope | Completed | — | — | N/A: no docs/00_index.md task-scope mapping for scripts/db/schema_sql.py |

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
- **Requirement ID**: REQ-001, REQ-002 (add per-consumer delivery-state and offset tables, second DDL source)
- **Source issue**: issues/20260907-125042_eb_h01_transactional_ack_offset_delivery_state.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20260909-094115_plan.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20260910-092106
- **Related target files**: scripts/db/schema_sql.py
