## Goal

Confirm `tests/agent/workflow/test_workflow_engine.py` carries no task key lookup (`REQ-003`, rename in tests).

## Scope

- Modify only `tests/agent/workflow/test_workflow_engine.py`.

## Assumptions

- Verified (Step 3a): the lookups by key were replaced by `get_task_by_id` in the earlier consolidation cycle (document `20261030-125133_01`); `rg idempotency_key tests/agent/workflow/test_workflow_engine.py` is empty now.
- This row therefore has no remaining edit unless the rename exposes one.
- Names that `tools/stale_detector.py` flags in this document are created by other rows of the same Plan or by an earlier row of it, and exist when `code-implementation` executes the rows in order.

## Design decisions

- N/A: lightweight test row.

## Alternatives considered

- N/A: lightweight test row.

## Implementation

### Target file

`tests/agent/workflow/test_workflow_engine.py`

### Procedure

1. Run `rg idempotency_key tests/agent/workflow/test_workflow_engine.py`; edit only if a reference remains.

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

- `uv run pytest tests/agent/workflow/test_workflow_engine.py -v`
- `uv run ruff check tests/agent/workflow/test_workflow_engine.py`

## Completion criteria

- `rg idempotency_key tests/agent/workflow/test_workflow_engine.py` is empty for the tasks table and the file passes.

## Out of Scope

- Other test files and the production code of the rename.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Update the references per Procedure | Completed | 20261030-173958 | 20261030-173958 | Plan Phase 3; verification only verification only: no key reference remained |
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
- **Related target files**: tests/agent/workflow/test_workflow_engine.py