## Goal

Rename the task key column in the workflow DDL of `scripts/db/schema_sql.py` and bump `WORKFLOW_SCHEMA_VERSION` (`REQ-003`, accurate key name; `REQ-004`, rename delivered with its migration).

## Scope

- Modify only `scripts/db/schema_sql.py`.

## Assumptions

- Verified (Step 3a, 2026-10-30): `idempotency_key  TEXT UNIQUE NOT NULL` is at `:179` in `_WORKFLOW_SCHEMA`, `WORKFLOW_SCHEMA_VERSION = "1.1.0"` at `:25`; `scripts/db/create_schema.py` (`_record_workflow_schema_version`) and `scripts/agent/services/workflow_schema.py` (`check_workflow_schema`) refuse a database whose recorded version differs, so the DDL rename, the version bump, and the registered migration (row 12 document) ship in one release.
- The dbmig001 registry exists (`scripts/db/migrations_workflow.py`, `scripts/shared/db_migrations.py`; Plan amendment 2026-10-30). Version chain: the registry is one linear chain, and `tests/db/test_migrations_workflow.py` asserts the last spec's `to_version` equals `WORKFLOW_SCHEMA_VERSION`. Default order: this Plan lands first, `1.1.0` to `1.2.0`. If `plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md` landed first, read `MIGRATIONS` and use the next version after its last `to_version`, and set the row 12 spec's `from_version` to it.
- The code rename (`models.py`, `task_ops.py`) and the test rows are one release unit with this row; execute in the Plan's Phase 3 order after the row 12 document's registry edit exists in the working tree, so the startup guard never sees a version without a path.
- Overlap judgment (Step 2, `check_plan_target_overlaps.py`): `schema_sql.py` is shared by Frozen Plans (toolexec001, ragcorpus001, wfrecovery001, wflease001, dbmig001): each edits a different table or constant; compatible, sequenced by rebasing.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of the same Plan or by an earlier row of it, and exist when `code-implementation` executes the rows in order.

## Design decisions

- Rename only the column in the `tasks` DDL and the version constant; keep `UNIQUE NOT NULL` so the contract (unique opaque value, never caller-derived) is unchanged.

## Alternatives considered

- Drop the column: rejected, it needs a table rebuild on SQLite 3.46.1 (Plan UNK-03).

## Implementation

### Target file

`scripts/db/schema_sql.py`

### Procedure

1. Change `idempotency_key  TEXT UNIQUE NOT NULL,` to `task_nonce        TEXT UNIQUE NOT NULL,` in the `tasks` table of `_WORKFLOW_SCHEMA`.
2. Set `WORKFLOW_SCHEMA_VERSION` to the next version in the chain (default `"1.2.0"`) and update the comment above it.

### Method

- Keep column alignment with the neighbouring lines.

### Details

- `RENAME COLUMN` keeps the unique index, so the canonical shape after the migration equals this DDL; the runner verifies that with the fingerprint (`verify_workflow_shape`).

## Compatibility considerations

- A database at the old version is refused at startup until `scripts/db/migrate_db.py --apply` has run; deployment order is in the deploy checklist.

## Security considerations

- N/A: DDL only.

## Rollback considerations

- Forward-only: after the migration has run, restore from the pre-migration backup the runner took; code revert alone does not undo the rename.

## Validation plan

- `uv run pytest tests/db/ tests/agent/workflow/ -v`
- `uv run ruff format scripts/db/schema_sql.py`, `uv run ruff check scripts/`, `uv run mypy --no-namespace-packages scripts/ tests/eventbus`, `PYTHONPATH=scripts uv run lint-imports`, `uv run bandit -r scripts/ -c pyproject.toml -ll`, `uv run python tools/check_module_size.py`
- `uv run python tools/check_db_separation.py`

## Completion criteria

- The DDL names the column `task_nonce`, `WORKFLOW_SCHEMA_VERSION` equals the last registered `to_version`, and no `idempotency_key` remains in `scripts/db/schema_sql.py` for the workflow tables.

## Out of Scope

- The registered spec (row 12), the code rename, tests, and docs.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Rename the column and bump the version | Completed | 20261030-173958 | 20261030-173958 | Plan Phase 3; with rows 03, 12 in one release unit column renamed, version 1.2.0 |
| 2 | Add or update tests per Validation plan | Completed | 20261030-173958 | 20261030-173958 | Covered by the row 09 and the other test rows' documents covered by rows 09 and 05-08 |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-173958 | 20261030-173958 | validators passed; full suite 10487 passed (wftaskapi001 release unit run); production workflow.sqlite mtime unchanged |

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
- **Requirement ID**: REQ-003, REQ-004
- **Source issue**: issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-125133
- **Related target files**: scripts/db/schema_sql.py