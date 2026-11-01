## Goal

Update `tests/agent/workflow/test_workflow_state_store.py` for the task-persistence consolidation: remove tests of deleted lookup APIs, rename key assertions to `task_nonce` (new), update raw INSERTs, and keep the duplicate-creation coverage explicit (Plan REQ-002, REQ-003, REQ-006).

## Scope

- Remove the `get_task_by_idempotency_key` import (`:23`) and the
  lookup-only tests `test_get_by_idempotency_key` and
  `test_get_by_idempotency_key_missing` (`:87-94`). Rewrite behavior tests
  that call the deleted lookup to use `get_task_by_id`:
  `test_retained_db_compatibility` (`:102-116`, lookup call at `:111`) and
  `test_update_status` (`:129-135`, lookup call at `:132`).
- Rename key assertions to `task_nonce` (new) (`:76-85`, `:121-125`) and every raw `INSERT INTO tasks (... idempotency_key ...)` (`:106`, `:265`, `:417`, `:467`, `:510`) — note `:106` disappears with its test.
- Keep/strengthen the duplicate-creation test (`:118-125` region): assert distinct `task_id` and distinct `task_nonce` (new) for two `create_task` calls with identical arguments (AC-5).

## Assumptions

- Remaining `idempotency_key` references at `:582-642` belong to `tool_call_state` (toolexec001) and MUST NOT be renamed (AC-3 scope note).
- Tests for `get_task_by_session`/`get_latest_task`/`list_tasks` do not
  exist in this file (re-verified 2026-11-01 by `rg`): the only deleted-API
  call sites here are `get_task_by_idempotency_key` at `:89`, `:94`, `:111`,
  `:132`.
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
| 1 | Implement the change described in Implementation > Procedure/Method/Details | In Progress | 2026-11-01 | — | cycle 1 done (lookup tests removed, get_task_by_id rewrites, REQ-006 assert); task_nonce renames deferred to cycle 2 |
| 2 | Add or update tests per Validation plan | Pending | — | — |  |
| 3 | Run the validation sequence (`rules/toolchain.md`) | In Progress | 2026-11-01 | — | cycle 1 validation passed; cycle 2 pending |

### Blocker Log
| Step | Blocker Description | Resolved | Resolution Date |
|------|---------------------|----------|-----------------|
| — | — | — | — |

### Verification Notes (2026-11-01)
- Passed with corrections: file is 646 lines; the legacy-composite test cite
  `:105-113` was stale — the actual test is `test_retained_db_compatibility`
  at `:102-116` (raw INSERT at `:106`, deleted-lookup call at `:111`).
  `test_update_status` at `:129-135` also calls the deleted lookup (`:132`)
  and is now in scope. Duplicate-creation test confirmed at `:118-125`
  (`test_state_store_create_task_issues_unique_keys`) — it asserts distinct
  keys but not distinct `task_id`; step 3 extends it.
- Raw INSERT column lists confirmed at `:106`, `:265`, `:417`, `:467`,
  `:510`. `tool_call_state` tests start at `TestToolCallStateOps` `:572` and
  run to `:642` — untouched (AC-3).
- Cycle split (shared row plan 01/02/05/06): import/lookup removal and the
  `get_task_by_id` rewrites run in cycle 1; the `task_nonce` renames in
  assertions and raw INSERTs run in cycle 2 (they require the renamed column
  and model field from rows 03/04).

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