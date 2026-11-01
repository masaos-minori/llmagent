## Goal

Replace the deleted `get_task_by_idempotency_key` lookups in `tests/agent/workflow/test_workflow_engine.py` with `get_task_by_id` (Plan REQ-002 delete zero-caller lookups).

## Scope

- Remove the import at `:20`; rewrite the four call sites at `:96`, `:127`, `:144`, `:298` (each `get_task_by_idempotency_key(store._db, task.idempotency_key)` / similar) to `get_task_by_id(store._db, task.task_id)` and assert on `task_nonce` (new) where the key value itself was asserted.

## Assumptions

- The four sites verify task identity after engine runs; switching to `get_task_by_id` preserves what they actually test (Plan Assumption: those tests verify only the lookup).
- `idempotency_key` uses at `:330-360` are `tool_call_state` transport-key tests (toolexec001) — untouched (AC-3 scope note).

## Design decisions

- Test-only rewrite; no engine behavior change asserted (AC-7: existing adapter and engine tests pass with renames only).

## Alternatives considered

- N/A: the API is deleted by REQ-002; keeping any call site is not an option.

## Implementation
### Target file
`tests/agent/workflow/test_workflow_engine.py`

### Procedure
1. Drop `get_task_by_idempotency_key` from the import line (`:20`); ensure `get_task_by_id` is imported from `agent.workflow.task_ops`.
2. At each of `:96`, `:127`, `:144`, `:298`, fetch via `get_task_by_id(store._db, task.task_id)`; where the old test also asserted the fetched row's `idempotency_key`, assert `task_nonce` (new) (a UUID4, Plan REQ-003 contract).

### Method
Mechanical rewrite; run the file after rows 01-05 land.

### Details
- Engine-side status-write assertions in this file (`workflow_engine.py:172-181` behavior) are unchanged by this Plan.

## Compatibility considerations

- Pairs with row 02's `StateStore` delegate changes; this file also exercises `StateStore` methods that keep their names.

## Security considerations

- N/A: test-only change.

## Rollback considerations

- N/A: revert the test commit.

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_engine.py -v` (AC-2, AC-7).
- `rg get_task_by_idempotency_key tests/agent/workflow/test_workflow_engine.py` → empty (AC-2).

## Completion criteria

- No reference to a deleted lookup API remains in this file; the four identity checks pass through `get_task_by_id` (AC-2).

## Out of Scope

- `tool_call_state` replay/dedup tests in this file (toolexec001-owned).

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

### Work Items Created
| Item ID | Related Step | Type | Status | Owner | Due Date |
|---------|--------------|------|--------|-------|----------|
| — | — | — | — | — | — |

## Traceability
- **Workflow phase**: plan-to-implementation-procedure
- **Requirement ID**: `REQ-002` (tests of deleted lookups removed / re-pointed)
- **Source issue**: issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-140834
- **Related target files**: tests/agent/workflow/test_workflow_engine.py
