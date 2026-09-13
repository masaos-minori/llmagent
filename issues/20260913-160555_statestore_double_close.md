# StateStore double-close risk in WorkflowEngineAdapter.execute_turn

## Priority
Medium

## Summary
Fix potential double-close of StateStore in `workflow_engine_adapter.py:execute_turn` when `_init_workflow_task` creates a new store but the outer finally block also closes it.

## Background
`_init_workflow_task` manages its own state store lifecycle: if `store=None`, it creates a new StateStore and sets `close_store=True`; if `store` is provided, it sets `close_store=False` to let the caller manage the store. However, `execute_turn` unconditionally calls `self._state_store.close()` in the finally block regardless of ownership.

## Problem
When `existing_task_id=None` (new workflow task), `_init_workflow_task` creates a new StateStore with `close_store=True` and closes it in its own finally block (line 305-306). Then `execute_turn`'s finally block closes `self._state_store` again (line 214), resulting in a double-close.

## Reason for Change
Double-close can cause undefined behavior depending on the underlying SQLite connection. While Python's sqlite3 module silently ignores subsequent close() calls, other database backends or future changes could raise exceptions or corrupt state.

## Implementation Intent
Pass a flag from `_init_workflow_task` indicating whether it owns the store, and skip the outer close in `execute_turn` when the inner method already closed it. Alternatively, restructure so `_init_workflow_task` returns the store reference along with a boolean indicating ownership.

## Target Files or Areas
- `/home/sugimoto/llmagent/scripts/agent/workflow_engine_adapter.py`

## Required Changes
- Modify `_init_workflow_task` to return `(workflow_id, task, store_closed)` tuple indicating whether it closed the store
- Update `execute_turn` to conditionally call `self._state_store.close()` based on the returned flag
- Update backward-compatible public API methods (`init_workflow_task`) to preserve existing return signature — move ownership tracking to a private attribute or separate return value

## Constraints
- Backward compatibility: public methods `init_workflow_task`, `activate_workflow`, etc. must not change their signatures
- Must not introduce any behavioral change for callers passing an existing `StateStore` instance

## Acceptance Criteria
- New workflow task creation does not double-close StateStore
- Existing workflow task resumption works without changing store ownership semantics
- No regressions in callers using the backward-compatible public API

## Testing Expectations
- Unit test covering `execute_turn` with `existing_task_id=None` verifying single close
- Unit test covering `execute_turn` with `existing_task_id` set verifying caller-owned store is not closed
- Regression test for backward-compatible public API methods

## Documentation Impact
Update docstrings for `_init_workflow_task` to clarify store ownership contract.

## Out of Scope
- Refactoring the entire execute_turn flow
- Adding new error handling paths

## Dependencies
N/A: none

## Unresolved Questions
- Does the current codebase have any callers relying on the double-close being silent?
- Should the outer close be removed entirely in favor of inner-method ownership?

## AI Implementation Instruction
Do not remove the outer close unconditionally — it protects against cases where `_init_workflow_task` receives a pre-opened store. Instead, track ownership via a returned boolean and conditionally apply the outer close.

## Traceability
- **Workflow phase**: python-code-review + issue-creator
- **Source issue**: N/A: this document is the issue
- **Source requirement**: N/A: no standalone requirement document is generated
- **Source plan**: N/A: not filed from a Plan
- **Source implementation procedure**: N/A: not filed from an implementation procedure
- **Generated at**: 20260913-160555
- **Related target files**: scripts/agent/workflow_engine_adapter.py
