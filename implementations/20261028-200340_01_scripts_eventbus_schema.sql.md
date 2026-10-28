## Goal
Add the partial unique index on `events.redelivered_from` to the canonical EventBus DDL and bump the schema stamp to version 2 (REQ-001: database-owned redelivery uniqueness).

## Scope
- Edit `scripts/eventbus/schema.sql` only: one `CREATE UNIQUE INDEX` statement and the `PRAGMA user_version` line.
- No change to `scripts/eventbus/schema.py`, `scripts/db/schema_sql.py` or `scripts/shared/eventbus_schema_fingerprint.py`; all three read this file (Reference files in the Plan).

## Assumptions
- `eventbus_schema_version()` parses the `PRAGMA user_version = {n};` line from this file (verified in the Plan cycle), so the bump needs no code change.
- The fingerprint already fingerprints indexes (name, unique, partial, key columns), so the new index automatically changes the expected fingerprint.
- Tests in `tests/eventbus/test_eventbus_schema_version.py` (seq 04) and the DDL copy in `tests/db/test_create_schema.py` (seq 05) carry the test-side updates; this document does not touch them.

## Design decisions
- Partial unique index (`WHERE redelivered_from IS NOT NULL`) instead of a table-level `UNIQUE`: ordinary events keep a NULL source and stay unconstrained; naming follows the existing `idx_events_*` pattern (`idx_events_redelivered_from` (new)).
- Version bump 1 → 2 in the same edit: without it, the fingerprint gate would reject new databases, and a stale 1-stamped file would keep its old shape semantics; per ADR-008 the refusal message already tells operators to recreate.

## Alternatives considered
- Table-level `UNIQUE(redelivered_from)` column constraint: rejected — identical guarantee for descendants but baked into the table definition, forcing a full table rewrite strategy for no benefit; the index form matches the file's existing style.
- Keeping version 1: rejected — old databases would silently pass the version gate and fail only the shape check with a less precise error.

## Implementation
### Target file
`scripts/eventbus/schema.sql`

### Procedure
1. After the existing `idx_events_dlq_seq` line (line 19), add:
   `CREATE UNIQUE INDEX IF NOT EXISTS idx_events_redelivered_from ON events(redelivered_from) WHERE redelivered_from IS NOT NULL;`
2. Change `PRAGMA user_version = 1;` (line 43) to `PRAGMA user_version = 2;`.

### Method
Text edit inside the existing `events` index block so the new index groups with its siblings; keep one statement per line and the file's column-alignment style.

### Details
- Current file has exactly four `events` indexes (lines 16-19) and no constraint on `redelivered_from TEXT` (line 10) — verified in the Plan cycle.
- The pragma statement is the last line of the file (line 43); `IF NOT EXISTS` matters because `_init_schema` executes the whole script on every `open_db` against an existing stamped-current database.

## Compatibility considerations
- Databases stamped 1 become refused at `open_db()` and `create_eventbus_schema()` with the existing "recreate the database" message (REQ-003, documented by seq 07); unstamped legacy databases keep their existing legacy handling.
- `CREATE INDEX IF NOT EXISTS` semantics make re-running the script on a version-2 database a no-op.

## Security considerations
N/A: DDL-only change; no new input handling. The fingerprint/`nosec` posture of the consumers is unchanged.

## Rollback considerations
Revert the two lines and recreate (or re-stamp) any database created by the new DDL: a 2-stamped database is refused by the rolled-back code, so rollback of a deployed environment requires the matching database recreate as well.

## Validation plan
- `uv run pytest tests/eventbus/test_eventbus_schema_version.py tests/db/test_create_schema.py -q` (after seq 04/05 updates land; run against the full sequence).
- `uv run python tools/check_db_separation.py`.
- `uv run pytest tests/eventbus tests/db tests/deploy -q`.

## Completion criteria
- A fresh `open_db` on a new file yields `PRAGMA user_version` 2 and an index named `idx_events_redelivered_from` (new) with unique=1 and a WHERE clause, visible via `PRAGMA index_list(events)`.
- The version-1 refusal test from seq 04 passes against this file.
- `check_db_separation.py` reports no finding.

## Out of Scope
- `dlq_repo.py` error mapping (seq 02), test updates (seq 03-05), docs (seq 06-08), any migration mechanism (Plan Out-of-Scope, ADR-008).

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
- **Requirement ID**: REQ-001 (schema.sql defines the partial unique index and stamps user_version 2)
- **Source issue**: issues/done/20261027-155850_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261028-194908_ebdlqunique007_enforce-dlq-redelivery-uniqueness.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261028-200340
- **Related target files**: scripts/eventbus/schema.sql
