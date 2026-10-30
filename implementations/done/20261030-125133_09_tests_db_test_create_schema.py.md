## Goal

Update `tests/db/test_create_schema.py` for the `task_nonce` rename and prove the registered migration preserves rows (`REQ-003`, rename in tests; `REQ-004`, migration with existing rows).

## Scope

- Modify only `tests/db/test_create_schema.py`.

## Assumptions

- Verified (Step 3a): the workflow DDL copy `_WORKFLOW_SCHEMA_NO_VEC0` starts at `:348` and names `idempotency_key` at `:359`; `test_tasks_idempotency_key_unique` is at `:502`. The migration framework tests already exist in `tests/shared/test_db_migrations.py` and `tests/db/test_migrations_workflow.py`; this row adds only the rename's own proof.
- Four Frozen Plans target this file: add a new test class and change only the lines the rename touches, to keep rebases trivial.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of the same Plan or by an earlier row of it, and exist when `code-implementation` executes the rows in order.

## Design decisions

- Run the real registry (`MIGRATIONS` from `db.migrations_workflow`) against a database built from the old DDL, not a test-local spec.

## Alternatives considered

- N/A: lightweight test row.

## Implementation

### Target file

`tests/db/test_create_schema.py`

### Procedure

1. Rename `idempotency_key` to `task_nonce` in the DDL copy and in `test_tasks_idempotency_key_unique` (rename the test to `test_tasks_task_nonce_unique`).
2. Add a class that creates a database from the previous-version tasks DDL (inline copy with `idempotency_key`), inserts rows, runs `run_migrations` with `WORKFLOW_DOMAIN` and `MIGRATIONS` to `WORKFLOW_SCHEMA_VERSION`, and asserts every row and its nonce value survive, the unique constraint still rejects a duplicate `task_nonce`, and the shape equals the canonical DDL.

### Method

- Use `tmp_path` databases and the module's existing helpers; no production paths.

### Details

- N/A: no further details beyond the other sections.

## Compatibility considerations

- Existing tests other than the renamed ones stay valid.

## Security considerations

- N/A: tests only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/db/test_create_schema.py tests/db/test_migrations_workflow.py -v`
- `uv run ruff check tests/db/test_create_schema.py`

## Completion criteria

- No `idempotency_key` remains for the tasks table in the file; the migration test passes and would fail without the registered spec.

## Out of Scope

- Other test files of the rename (rows 05-08).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the tests per Procedure | Completed | 20261030-173958 | 20261030-173958 | Plan Phase 3; with rows 04 and 12 tests renamed; TestTaskNonceMigration added |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-173958 | 20261030-173958 | validators passed; full suite 10487 passed (wftaskapi001 release unit run); production workflow.sqlite mtime unchanged |

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
- **Related target files**: tests/db/test_create_schema.py