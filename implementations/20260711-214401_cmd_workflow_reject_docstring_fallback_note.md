# Implementation Procedure: cmd_workflow.py — document engine-side rejection fallback in `_cmd_reject()` docstring

Source plan: `plans/20260711-173259_plan.md` — Design §2 / Implementation step 4b

## Goal

Add a docstring note to `_cmd_reject()` explaining that `WorkflowEngine._gate_approval()` also halts on a rejected-status approval record as a defensive fallback, so a future reader understands the two halt paths are intentionally redundant, not conflicting.

## Scope

**In:**
- `scripts/agent/commands/cmd_workflow.py::_cmd_reject()`: docstring addition only.

**Out:**
- No change to `_cmd_reject()`'s actual implementation (`resolve_approval(..., "rejected", ...)` followed by `update_task_status(store._db, task_id, "halted")`) — already correct and already tested (`tests/test_cmd_workflow_approval.py::test_reject_halts_task`).
- No change to the `"Use '/workflow status'..."` line removal — that is a separate, already-completed sibling item (see `implementations/20260711-172557_cmd_workflow_remove_workflow_status_reference.md`, a different plan's scope); do not re-touch that line here, only add the new fallback-note sentence.

## Assumptions

1. Confirmed by direct read: `_cmd_reject()` (lines 159-160) already calls `resolve_approval(..., "rejected", ...)` immediately followed by `update_task_status(store._db, task_id, "halted")` — this is the primary, common-case halt path.
2. `WorkflowEngine._gate_approval()`'s own `rejected`-status branch (companion doc `20260711-214340_workflow_engine_rename_call_site_and_defensive_comment.md`) is a defensive fallback for cases where the engine re-evaluates a task whose approval was resolved as `"rejected"` through some path other than this command — confirmed via the plan's Assumption 3.
3. A sibling, already-processed plan (`implementations/20260711-172557_cmd_workflow_remove_workflow_status_reference.md`) touches this same file/function's validation-error message and module docstring — a **different** part of the file. This item only adds a new sentence to `_cmd_reject()`'s own docstring; verify at implementation time that the sibling item's edits have not shifted line numbers before locating the exact insertion point.

## Implementation

### Target file

`scripts/agent/commands/cmd_workflow.py`

### Procedure

1. Locate `_cmd_reject()`'s docstring (current first lines: "Reject the pending workflow-level approval gate (approvals table only)." / "Does not affect per-tool interactive approval (tool_approval.run_approval_checks)." / "Immediately marks the task as halted.").
2. Append one new sentence at the end of the existing docstring:
   ```python
   def _cmd_reject(self, arg: str) -> None:
       """Reject the pending workflow-level approval gate (approvals table only).

       Does not affect per-tool interactive approval (tool_approval.run_approval_checks).
       Immediately marks the task as halted. WorkflowEngine._gate_approval() also
       halts on a rejected-status approval record as a defensive fallback for
       resume paths that don't go through this command.
       """
   ```
3. Do not modify any other line of the docstring or the function body.

### Method

Single docstring text addition (one new sentence appended). No code/logic change.

### Details

- Confirm the exact current docstring text via a direct read immediately before editing, since a sibling plan's changes to this same file may have shifted surrounding line numbers.
- Keep the added sentence factual and pointing at the actual class/method name (`WorkflowEngine._gate_approval()`) so it stays a useful cross-reference, not a vague comment.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to this file:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/commands/cmd_workflow.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/commands/cmd_workflow.py` | No new errors |
| Tests | `uv run pytest tests/test_cmd_workflow.py tests/test_cmd_workflow_approval.py -v` | All pass (docstring-only change, no behavior regression expected) |
