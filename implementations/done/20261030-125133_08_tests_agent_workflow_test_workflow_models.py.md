## Goal

Rename the `TaskRecord` constructor argument in `tests/agent/workflow/test_workflow_models.py` to `task_nonce` (`REQ-003`, rename in tests).

## Scope

- Modify only `tests/agent/workflow/test_workflow_models.py`.

## Assumptions

- Verified (Step 3a): `idempotency_key="s1:3"` at `:30` constructs a `TaskRecord`; the field is renamed by the row 03 document.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of the same Plan or by an earlier row of it, and exist when `code-implementation` executes the rows in order.

## Design decisions

- N/A: lightweight test row.

## Alternatives considered

- N/A: lightweight test row.

## Implementation

### Target file

`tests/agent/workflow/test_workflow_models.py`

### Procedure

1. Change the keyword to `task_nonce=` (the value stays a plain string in this model test).

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

- `uv run pytest tests/agent/workflow/test_workflow_models.py -v`
- `uv run ruff check tests/agent/workflow/test_workflow_models.py`

## Completion criteria

- `rg idempotency_key tests/agent/workflow/test_workflow_models.py` is empty for the tasks table and the file passes.

## Out of Scope

- Other test files and the production code of the rename.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the references per Procedure | Completed | 20261030-173958 | 20261030-173958 | Plan Phase 3; with row 03 constructor argument renamed |
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
- **Related target files**: tests/agent/workflow/test_workflow_models.py