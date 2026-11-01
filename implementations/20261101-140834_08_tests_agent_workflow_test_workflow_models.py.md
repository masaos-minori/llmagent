## Goal

Rename the `TaskRecord` constructor argument in `tests/agent/workflow/test_workflow_models.py` to `task_nonce` (new) (Plan REQ-003 model rename in tests).

## Scope

- `TaskRecord(..., idempotency_key="s1:3", ...)` at `:25` becomes `task_nonce="s1:3"`; assertions naming the attribute in the same and neighboring tests are renamed with it.

## Assumptions

- Re-verified 2026-11-01: cite `:25` exact. The composite-looking value `"s1:3"` is deliberate in the test (it proves the stored value is treated as opaque); keep the value, rename the argument.

## Design decisions

- Rename-in-place; `TestTaskRecord.test_create` keeps its structure (the Plan's "`:61-119` round-trip/payload tests" cite is stale — see Verification Notes).

## Alternatives considered

- N/A: mechanical rename forced by row 03's model change.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_models.py`

### Procedure
1. Rename the constructor kwarg at `:25` and any `record.idempotency_key` assertions in tests that construct `TaskRecord`.

### Method
Mechanical rename; land with row 03.

### Details
- If a test asserts the attribute set of `TaskRecord`, `task_nonce` (new) replaces `idempotency_key` there as well.

## Compatibility considerations

- None beyond row 03 pairing.

## Security considerations

- N/A: test-only change.

## Rollback considerations

- N/A: revert the commit.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_models.py -v` (AC-3).

## Completion criteria

- No task-key `idempotency_key` reference remains in this file; model tests pass against the renamed `TaskRecord` (AC-3).

## Out of Scope

- Attempt/payload model tests unrelated to the task key.

## Execution Status

### Execution Status
| Step | Description | Status | Started | Completed | Notes |
|------|-------------|--------|---------|-----------|-------|
| 1 | Implement the change described in Implementation > Procedure/Method/Details | Pending | — | — | |
| 2 | Add or update tests per Validation plan | Pending | — | — | |
| 3 | Run the validation sequence (`rules/toolchain.md`) | Pending | — | — | |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Verification Notes (2026-11-01)
- Passed with correction: `TaskRecord(..., idempotency_key="s1:3")` at `:25`
  confirmed (test file 100 lines). The Plan's "`:61-119` round-trip/payload
  tests" do not exist in this file — the only task-key reference is `:25` in
  `TestTaskRecord.test_create` (`:17-31`). No attribute-set test exists.
- Cycle: cycle 2 only (lands with row 03's model rename).

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-003` (rename-aware model test)
- **Source issue**: issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-140834
- **Related target files**: tests/agent/workflow/test_workflow_models.py
