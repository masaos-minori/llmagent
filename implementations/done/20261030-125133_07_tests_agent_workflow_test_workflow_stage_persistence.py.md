## Goal

Rename the task key column in the raw task INSERT of `tests/agent/workflow/test_workflow_stage_persistence.py` (`REQ-003`, rename in tests).

## Scope

- Modify only `tests/agent/workflow/test_workflow_stage_persistence.py`.

## Assumptions

- Verified (Step 3a): the raw `INSERT INTO tasks (task_id, workflow_id, workflow_ve...` statement at `:29` names `idempotency_key`; the DDL comes from `build_workflow_schema_sql()`, so it follows the DDL rename (row 04 document).
- Names that `tools/stale_detector.py` flags in this document are created by other rows of the same Plan or by an earlier row of it, and exist when `code-implementation` executes the rows in order.

## Design decisions

- N/A: lightweight test row.

## Alternatives considered

- N/A: lightweight test row.

## Implementation

### Target file

`tests/agent/workflow/test_workflow_stage_persistence.py`

### Procedure

1. Change the column name in the INSERT statement to `task_nonce`.

### Method

- Change only the lines named in Procedure; keep neighbouring tests untouched.

### Details

- Fallout of the rename outside the Plan's rows (the new tests of the earlier recovery work and the registry tests) is corrected in the same release unit and recorded in the Execution Status Notes of the row 04 document.

## Compatibility considerations

- Existing tests other than the renamed references stay valid.

## Security considerations

- N/A: tests only.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_stage_persistence.py -v`
- `uv run ruff check tests/agent/workflow/test_workflow_stage_persistence.py`

## Completion criteria

- `rg idempotency_key tests/agent/workflow/test_workflow_stage_persistence.py` is empty for the tasks table and the file passes.

## Out of Scope

- Other test files and the production code of the rename.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the references per Procedure | Completed | 20261030-173958 | 20261030-173958 | Plan Phase 3; with rows 04 and 12 raw INSERT renamed |
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
- **Requirement ID**: REQ-003
- **Source issue**: issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261030-125133
- **Related target files**: tests/agent/workflow/test_workflow_stage_persistence.py