## Goal

Extend `tests/db/test_create_schema.py` with the schema constraint and migration proofs for the recovery schema (`REQ-008`, constraints; `REQ-011`, migration of databases with valid and invalid rows).

## Scope

- Modify only `tests/db/test_create_schema.py`.

## Assumptions

- Verified (Step 3a): the workflow DDL copy `_WORKFLOW_SCHEMA_NO_VEC0` starts at `:348` and lacks the new constraints; the module patches `build_workflow_schema_sql` with it in several tests, so after the DDL change this copy must carry the same `CHECK`, `attempt_number`, index, and ledger columns or the baseline-insert and version tests fail.
- Four Frozen Plans target this file: add a new class and update the copy; do not reformat neighbouring tests.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of the same Plan or by an earlier row of it, and exist when `code-implementation` executes the rows in order.

## Design decisions

- Test the real registry against a database built from the previous-version DDL with rows, as in the wftaskapi001 row 09 document.

## Alternatives considered

- N/A: lightweight test row.

## Implementation

### Target file

`tests/db/test_create_schema.py`

### Procedure

1. Update `_WORKFLOW_SCHEMA_NO_VEC0` to the new DDL shape (constraints, `attempt_number`, index, `processed_events` columns).
2. Add tests for: the SQL status vocabulary equals `TaskStatus` and `AttemptStatus` values (REQ-001); a raw insert with an unknown status is rejected for both tables; `attempt_number` is unique per task-stage pair; migration of a previous-version database with valid rows keeps tasks, attempts, and completed-stage ledger rows, backfills `attempt_number` by started order, and keeps `attempts` rows when `tasks` is rebuilt; started-only `processed_events` rows are dropped; a database with an unknown status is refused by the precondition and left byte-identical; `PRAGMA foreign_key_check` is empty after migration.

### Method

- Use `tmp_path` databases; build previous-version fixtures from inline DDL, not from the new canonical DDL.

### Details

- N/A: no further details beyond the other sections.

## Compatibility considerations

- Existing tests other than the DDL copy stay valid.

## Security considerations

- N/A: tests only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/db/test_create_schema.py tests/db/test_migrations_workflow.py -v`
- `uv run ruff check tests/db/test_create_schema.py`

## Completion criteria

- The listed cases pass and fail without the DDL change or the registered spec; the DDL copy matches the canonical DDL.

## Out of Scope

- Agent-layer tests (other rows).

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update and add the tests per Procedure | Completed | 20261030-183035 | 20261030-183035 | Plan Phase 2; with rows 10 and 26 done in batch |
| 2 | Run the validation sequence (`rules/toolchain.md`) | Completed | 20261030-183035 | 20261030-183035 | executed in the Plan Phase 2-4 single batch; full suite 10516 passed, 1 unrelated flaky eventbus 503 (passes alone); production workflow.sqlite mtime unchanged |

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
- **Requirement ID**: REQ-008, REQ-011
- **Source issue**: issues/20261030-105639_wfrecovery001_workflow-recovery-state-machine.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-114041_wfrecovery001_workflow-recovery-state-machine.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-125334
- **Related target files**: tests/db/test_create_schema.py