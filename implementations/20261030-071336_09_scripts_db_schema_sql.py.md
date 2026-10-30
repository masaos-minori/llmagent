## Goal
Add the `schema_migrations` ledger table DDL to the workflow DDL set in `scripts/db/schema_sql.py` so every newly created `workflow.sqlite` is ledger-compatible, while `WORKFLOW_SCHEMA_VERSION` stays the baseline marker (REQ-001 migration framework, REQ-006 ledger in every canonical database).

## Scope
- In scope: `_WORKFLOW_SCHEMA` DDL text and, if needed for reuse, a ledger DDL constant in `scripts/db/schema_sql.py`.
- Out of scope: ledger DDL for `eventbus.sqlite` (row 04), baseline row insertion (row 08), registry/version-code map (row 06), the rag/session DDL templates (recreate-only policy, unchanged).

## Current shape (facts)
- `_WORKFLOW_SCHEMA` (`scripts/db/schema_sql.py:168-218`) is inline Python-string DDL containing `tasks`, `attempts`, `processed_events`, `artifacts`, and the string version log `workflow_schema_version` (`:214-217`). There is no separate workflow `.sql` file; `build_workflow_schema_sql()` (`:244-246`) returns this string verbatim.
- `WORKFLOW_SCHEMA_VERSION = "1.1.0"` (`:25`) and the `workflow_schema_version` table stay untouched (Plan Assumption: the string marker remains the baseline).
- `eventbus_schema_version()` (`:227-236`) parses the stamp from `scripts/eventbus/schema.sql` at runtime; row 04's stamp change needs no change here.

## Assumptions
- The ledger column contract is fixed by the Plan (`schema_migrations(id TEXT PRIMARY KEY, applied_at TEXT, from_version INTEGER, to_version INTEGER)`) and must be byte-equivalent in intent to row 01's `LEDGER_CREATE_SQL` and row 04's eventbus DDL.
- No `PRAGMA user_version` line is added to `_WORKFLOW_SCHEMA`: workflow version bookkeeping stays string-log + ledger (row 06 decision), and adding a second stamp mechanism is out of scope.

## Design decisions
- Append a `CREATE TABLE IF NOT EXISTS schema_migrations` block inside `_WORKFLOW_SCHEMA` after `workflow_schema_version`; keep it `IF NOT EXISTS` so re-execution against an existing workflow database stays idempotent, matching the file's existing style.

## Alternatives considered
- Moving workflow DDL to a dedicated `.sql` file to mirror eventbus — rejected: unrelated structural churn for this issue (repo rule: change only what the task requires).

## Implementation
### Target file
- `scripts/db/schema_sql.py`

### Procedure
1. Append the ledger DDL block to `_WORKFLOW_SCHEMA` per Design.
2. Keep the module docstring's function list accurate; update the "Functions" comment only if wording references table lists.
3. Do not touch `_RAG_SCHEMA_TEMPLATE`, `_SESSION_SCHEMA_TEMPLATE`, `eventbus_schema_version`, or `build_eventbus_schema_sql`.

### Method
One additive DDL edit inside an existing string constant.

### Details
- Row 06's `workflow_ledger_baseline` mutation text and row 01's ledger primitive must produce the identical table shape; `tests/db/test_migrations_workflow.py` (row 17) asserts `PRAGMA table_info` equality between a baseline-created and a migrated workflow database.

## Compatibility considerations
- `create_workflow_schema` executes the updated DDL unchanged (`create_schema.py:100`); `deploy/init_db.sh`'s required-table loop (row 13 extends it) currently checks only `tasks attempts processed_events artifacts` (`deploy/init_db.sh:46`), which stays valid.

## Security considerations
- N/A: static DDL, no input paths.

## Rollback considerations
- Revert the commit; databases already created with the ledger table keep it (inert without the runner).

## Validation plan
- `uv run pytest tests/db/test_create_schema.py tests/db/test_migrations_workflow.py` (rows 18/17 assert the ledger surface).
- `uv run mypy --no-namespace-packages scripts/`.

## Completion criteria
- `build_workflow_schema_sql()` output creates `schema_migrations` with the Plan's exact column contract; a fresh workflow database has both `workflow_schema_version` and `schema_migrations`; existing tests that inspect the DDL string are updated only where they enumerate tables.

## Out of Scope
- eventbus DDL (row 04), baseline rows (row 08), CLI (row 07), docs (rows 20-23).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | Tests come from rows 17/18 |
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
- **Related target files**: `scripts/db/schema_sql.py`
