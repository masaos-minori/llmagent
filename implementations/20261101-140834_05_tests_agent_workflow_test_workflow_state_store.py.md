## Goal

Update `tests/agent/workflow/test_workflow_state_store.py` for the task-persistence consolidation: remove tests of deleted lookup APIs, rename key assertions to `task_nonce` (new), update raw INSERTs, and keep the duplicate-creation coverage explicit (Plan REQ-002, REQ-003, REQ-006).

## Scope

- Remove `get_task_by_idempotency_key` import (`:23`) and the lookup-only tests (`test_get_by_idempotency_key` `:87-94`, its missing-key variant `:93-94`, and the legacy-composite-key test at `:105-113` that depends on the deleted lookup).
- Rename key assertions to `task_nonce` (new) (`:76-85`, `:121-125`) and every raw `INSERT INTO tasks (... idempotency_key ...)` (`:106`, `:265`, `:417`, `:467`, `:510`) — note `:106` disappears with its test.
- Keep/strengthen the duplicate-creation test (`:118-125` region): assert distinct `task_id` and distinct `task_nonce` (new) for two `create_task` calls with identical arguments (AC-5).

## Assumptions

- Remaining `idempotency_key` references at `:582-642` belong to `tool_call_state` (toolexec001) and MUST NOT be renamed (AC-3 scope note).
- Tests for `get_task_by_session`/`get_latest_task`/`list_tasks` are located by `rg` at implementation time and removed with the APIs; any surviving behavior test must switch to `get_task_by_id` or the retained aggregates.
- This file also holds tool-call-state tests (`:582-642`) unrelated to this Plan — leave them untouched.

## Design decisions

- Rename-in-place rather than rewriting tests: existing assertions encode the UUID4/never-composite contract, which is unchanged (REQ-003 contract preservation).

## Alternatives considered

- Keeping a test that verifies the deleted lookups via `task_ops`: rejected (REQ-002 deletes the APIs; AC-2 forbids the names repo-wide).

## Implementation
### Target file
`tests/agent/workflow/test_workflow_state_store.py`

### Procedure
1. Delete the import at `:23` and the lookup-only tests named above.
2. Replace `idempotency_key` with `task_nonce` (new) in task-side assertions and raw INSERT column lists (task-side occurrences only).
3. Confirm the duplicate-creation test asserts both distinct `task_id` and distinct `task_nonce` (new) after `create_task` with identical arguments; extend it if the `task_id` assertion is missing (REQ-006).

### Method
Text rename plus targeted test deletion; run the file's tests after rows 01-04 land (delegates and rename must be in place first).

### Details
- The `:265/:417/:467/:510` INSERTs are fixture helpers for stale/attempt and diagnostic tests — only the column name changes.
- Aggregate-count tests continue to exercise the `StateStore` delegates updated in row 02.

## Compatibility considerations

- Tests here reference `StateStore` 84+ times (Plan Risks); only the renamed/deleted APIs change.
- Land after rows 01-04 land; before them the renamed column does not exist.

## Security considerations

- N/A: test-only change.

## Rollback considerations

- N/A: revert the test commit (Phase 2 / Phase 3 test updates follow the Plan's phase split).

## Validation plan

- `uv run pytest tests/agent/workflow/test_workflow_state_store.py -v` (AC-2, AC-3, AC-5).
- `rg "get_task_by_idempotency_key|get_task_by_session|get_latest_task|list_tasks" tests/agent/workflow/test_workflow_state_store.py` → empty (AC-2).

## Completion criteria

- No task-side `idempotency_key` text remains in this file; no deleted API is imported or called; a duplicate-creation test proves distinct `task_id`/`task_nonce` (new) (AC-2, AC-3, AC-5).

## Out of Scope

- `tool_call_state` tests (`:582-642`); attempt/stale-recovery test semantics (wflease001 territory).

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
- **Requirement ID**: `REQ-002` (deleted-API tests), `REQ-003` (key rename), `REQ-006` (duplicate-creation behavior)
- **Source issue**: issues/20261030-105723_wftaskapi001_consolidate-task-persistence.md
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: plans/20261030-113553_wftaskapi001_consolidate-task-persistence.md
- **Source implementation procedure**: N/A: this document is the generated implementation procedure
- **Generated at**: 20261101-140834
- **Related target files**: tests/agent/workflow/test_workflow_state_store.py
