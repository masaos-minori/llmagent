## Goal
Make the new-database creation path in `scripts/db/create_schema.py` ledger-compatible: each created database additionally gets the `schema_migrations` ledger and a baseline ledger row, while every existing-database mismatch keeps today's fail-closed refusal (REQ-001 migration framework, REQ-006 ledger in every canonical database).

## Scope
- In scope: `create_workflow_schema` and `create_eventbus_schema` in `scripts/db/create_schema.py`; baseline stamping for fresh databases only.
- Out of scope: startup-time migration of existing databases (eventbus startup is row 03; existing workflow databases are upgraded by the row 07 CLI), ledger DDL definitions (rows 04, 09), registry content (rows 02, 06).

## Assumptions
- Today's behaviors preserved verbatim: `_record_workflow_schema_version` refusal for a mismatched string (`create_schema.py:53-78`), `create_eventbus_schema`'s version-mismatch refusal (`create_schema.py:113-117`), the unstamped-legacy `user_version 0` branch that stays unstamped until the service verifies shape (`create_schema.py:123-126`), and the already-stamped `assert_matches` gate (`create_schema.py:130`).
- After row 04, `eventbus_schema_version()` returns 4 automatically (it parses `scripts/eventbus/schema.sql` at `schema_sql.py:227-236`); a deployed database still stamped 3 is refused by this create path until upgraded through the row 05 CLI — that sequencing is documented by row 13, not hidden here.
- Ledger baseline rows use row 01's id conventions (`eventbus_ledger_baseline`, `workflow_ledger_baseline`) with `from_version == to_version` for a freshly created database (baseline stamp, no migration executed).

## Design decisions
- Baseline insertion is idempotent and delegated to the registries: `migrations_workflow.ensure_baseline(conn)` (row 06) for workflow; for eventbus, a baseline `INSERT OR IGNORE` through row 01's ledger primitive executed right after a fresh/stamped database passes its gate — the create path never re-implements ledger DDL (it comes from rows 04/09's DDL sets).
- rag.sqlite and session.sqlite keep the recreate-only policy (ADR-008 as amended by row 20): no ledger rows are added to their create functions in this issue.

## Alternatives considered
- Running the migration runner at workflow creation time for fresh databases — rejected: a fresh database has nothing to migrate; a baseline row insert is the ledger-compatible equivalent and keeps `create_schema.py` free of runner wiring.

## Implementation
### Target file
- `scripts/db/create_schema.py`

### Procedure
1. In `create_workflow_schema` (`create_schema.py:97-103`): after `_record_workflow_schema_version(db)`, call `migrations_workflow.ensure_baseline(db.conn)` (new wiring) before `db.commit()`.
2. In `create_eventbus_schema` (`create_schema.py:106-132`): on the fresh path (no `events` table before the script) and on the already-stamped path that passes `assert_matches`, insert the `eventbus_ledger_baseline` row idempotently via the row-01 ledger primitive; leave the `user_version 0` legacy branch untouched.
3. Keep the module docstring and function docstrings accurate about the refusal semantics they retain.

### Method
Additive wiring inside existing functions; imports limited to `db.migrations_workflow` (same layer) and `shared.db_migrations` ledger primitives. No signature changes.

### Details
- The ledger tables exist before insertion because row 09 adds the workflow ledger DDL to `_WORKFLOW_SCHEMA` and row 04 adds it to `scripts/eventbus/schema.sql`; land rows 04/09 before this row in `seq` order.

## Compatibility considerations
- Databases created before this change have no baseline ledger row; the row 02/06 bootstrap steps register them on their next upgrade. Existing operators' `python db/create_schema.py` invocation behavior is unchanged except for the added ledger rows.

## Security considerations
- No new input surface; all SQL is repo-authored static text.

## Rollback considerations
- Revert the commit; databases already carrying baseline ledger rows remain readable by the reverted code (the ledger table is inert without the runner).

## Validation plan
- `uv run pytest tests/db/test_create_schema.py` (row 18 extends: fresh workflow/eventbus databases carry ledger + baseline row; refusal cases unchanged).
- Characterization: current refusal tests in `tests/db/test_create_schema.py` stay green.
- `lint-imports`; `uv run mypy --no-namespace-packages scripts/`.

## Completion criteria
- A fresh run against an empty directory yields four databases where `workflow.sqlite` and `eventbus.sqlite` contain `schema_migrations` with exactly one baseline row; a pre-existing mismatched database is still refused with the same messages.

## Out of Scope
- Existing-database migration execution (rows 03/05/07), deploy script sequencing (row 13), rag/session policy (unchanged).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests come from row 18 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |
| 4 | Update documentation, if in scope per Compatibility/Out of scope | Pending | — | — | N/A for this row |

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
- **Related target files**: `scripts/db/create_schema.py`
