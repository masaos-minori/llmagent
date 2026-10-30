## Goal
Add the `schema_migrations` ledger table DDL to `scripts/eventbus/schema.sql` and raise the baseline `PRAGMA user_version` stamp from 3 to 4, making the baseline the post-migration fingerprint source for `eventbus.sqlite` (REQ-001 migration framework, REQ-006 ledger in every canonical database).

## Scope
- In scope: baseline DDL file only — ledger table DDL plus the version stamp.
- Out of scope: the registered `3 → 4` step that upgrades existing databases (row 02), startup wiring (row 03).

## Assumptions
- Fingerprint source: `scripts/shared/eventbus_schema_fingerprint.py` derives the canonical shape from this file at runtime (verified), so no fingerprint-module edit is needed — the ledger table becomes part of the canonical shape by definition.
- `scripts/db/schema_sql.py::eventbus_schema_version()` parses the stamp from this file (`schema_sql.py:227-236`), so version consumers pick up 4 automatically; no `db`-layer code change.
- Cross-plan: `plans/20261029-221254_dlqbox001_dlq-sqlite-outbox.md` also targets this file later for `dlq_outbox` and stamps "the version after the dbmig001 ledger step" — sequenced dependency (dbmig001 first), not a contradiction.

## Design decisions
- Ledger column contract identical to row 01 (`schema_migrations(id TEXT PRIMARY KEY, applied_at TEXT, from_version INTEGER, to_version INTEGER)`) so baseline-created and migrated databases are shape-identical.

## Alternatives considered
- N/A: DDL shape fixed by the Plan's ledger contract.

## Implementation
### Target file
- `scripts/eventbus/schema.sql`

### Procedure
1. Append `CREATE TABLE IF NOT EXISTS schema_migrations` (new table) DDL per the row-01 contract after the existing table definitions.
2. Change the stamp line `PRAGMA user_version = 3;` (`schema.sql:45`) to `PRAGMA user_version = 4;`.
3. Keep comments in the file consistent (file header/version comments if any reference 3).

### Method
Two additive text edits; apply before the row-02 registry commit lands (same commit, DDL first).

### Details
- `tests/db/test_eventbus_schema_equivalence.py` compares db-layer and eventbus-layer views of this file; it must still pass.
- Existing databases at version 3 will now fail `assert_matches` (missing ledger table) — intentional: they must take the registered bootstrap migration (rows 02/03), never a silent pass.

## Compatibility considerations
- Version bump is visible to `eventbus_schema_version()` consumers (`create_schema.py` refusal comparison, `tests/eventbus/test_eventbus_schema_version.py` pin test — row 16 updates it).

## Security considerations
- N/A: static DDL, no input paths.

## Rollback considerations
- Revert the commit; databases already migrated to 4 become refused at startup (pre-change refuse-only contract) — restore requires re-land, not silent downgrade.

## Validation plan
- `uv run pytest tests/db/test_eventbus_schema_equivalence.py tests/eventbus/test_eventbus_schema_version.py`.
- `uv run python tools/check_db_separation.py`.

## Completion criteria
- Fresh databases created from this file carry `schema_migrations` and stamp 4; the fingerprint, `eventbus_schema_version()`, and the registry bootstrap step agree on version 4.

## Out of Scope
- Registry/CLI/startup code, workflow ledger DDL (rows 02/03/05/09).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Completed | 20261030-084500 | 20261030-084500 | Already implemented in the row-02 commit (5b301eecb): ledger DDL (id/applied_at/from_version/to_version identical to row-01 contract) plus PRAGMA user_version = 4 baseline stamp. |
| 2 | Add or update tests per Validation plan | Completed | 20261030-084500 | 20261030-084500 | Updated by rows 15/16 Covered by tests/db/test_eventbus_schema_equivalence.py + tests/eventbus/test_eventbus_schema_version.py (13 passed). |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-084500 | 20261030-084500 | equivalence+version 13 passed; db+deploy 364 passed earlier. |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Completed | 20261030-084500 | 20261030-084500 | N/A for this row N/A: no docs/00_index.md task-scope mapping for schema.sql. |

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
- **Requirement ID**: `REQ-001` (migration framework), `REQ-006` (ledger)
- **Source issue**: `issues/20261029-104500_dbmig001_forward-only-db-migrations.md`
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: `plans/20261029-214108_dbmig001_forward-only-db-migrations.md`
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-071336
- **Related target files**: `scripts/eventbus/schema.sql`