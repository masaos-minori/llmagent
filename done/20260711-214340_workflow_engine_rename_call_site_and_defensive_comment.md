# Implementation Procedure: workflow_engine.py — update rename call site + defensive-duplication comment

Source plan: `plans/20260711-173259_plan.md` — Design §1 (call-site) and Design §2 (comment) / Implementation steps 2, 4a

## Goal

Update `WorkflowEngine._gate_approval()`'s import and call site to use the renamed `get_latest_approval()` (companion doc `20260711-214322_approval_ops_rename_get_latest_approval.md`), and add a comment explaining that its `rejected`-status branch is an intentional defensive fallback, not a conflicting duplicate of `/reject`'s immediate halt.

## Scope

**In:**
- `scripts/agent/workflow/workflow_engine.py` line 18 (import) and line 143 (call site): `get_pending_approval` → `get_latest_approval`.
- `scripts/agent/workflow/workflow_engine.py::_gate_approval()`'s `if existing.status == "rejected":` branch (~lines 166-168): add an explanatory comment above it.

**Out:**
- No change to `_gate_approval()`'s actual control flow, branching logic, or the `approved`/`pending` branches — only the import/call-site name and one new comment.
- No new test in this file — test coverage for the rejected-branch behavior already exists (`tests/test_workflow_engine.py::test_rejected_task_halts`); this item is documentation-only for that branch.

## Assumptions

1. Confirmed by direct read: `workflow_engine.py:18` imports `get_pending_approval` from `approval_ops`; `workflow_engine.py:143` calls it inside `_gate_approval()`. Both must change to `get_latest_approval` in lockstep with the rename in `approval_ops.py` (companion doc), or the module fails to import.
2. Confirmed by direct read of `workflow_engine.py:166-168`: the `rejected`-status branch calls `self._store.update_task_status(task.task_id, "halted")` then raises `WorkflowHaltError`. This is functionally correct and already tested — the only gap is that its *purpose* (a defensive fallback for a case where an approval was resolved as `"rejected"` outside the `/reject` command path) is undocumented in the code itself.
3. No test or code path today exercises "rejected-in-DB but task not yet halted" as a race condition — this is genuinely defensive per the plan's Assumption 3, not evidence of an actual conflict between `/reject` and this branch. No new test is required for this comment-only change (per the plan's Risk analysis: documentation, not new test coverage, is what's asked).

## Implementation

### Target file

`scripts/agent/workflow/workflow_engine.py`

### Procedure

1. Update the import at line 18: `get_pending_approval` → `get_latest_approval`.
2. Update the call site at line 143 (inside `_gate_approval()`): `get_pending_approval(...)` → `get_latest_approval(...)`, keeping arguments unchanged.
3. Immediately above the `if existing.status == "rejected":` branch (~line 166), add the comment block exactly as specified in the plan's Design §2:
   ```python
   if existing.status == "rejected":
       # Defensive fallback: /reject (cmd_workflow.py) already halts the task
       # immediately when the user rejects. This branch only fires if the
       # engine re-evaluates a task whose approval was resolved as "rejected"
       # through some other path before the halt was applied.
       self._store.update_task_status(task.task_id, "halted")
       raise WorkflowHaltError(f"approval rejected: {existing.reason}")
   ```
4. Do not alter the `update_task_status(...)` call or the `WorkflowHaltError` message/formatting — only the comment is new.

### Method

Two mechanical identifier renames (import + one call site) plus a single explanatory comment block inserted above existing, unchanged code. No control-flow or behavior change.

### Details

- This file's rename must land in the same review/commit unit as `approval_ops.py`'s rename (companion doc) — an import mismatch between the two would break at module-import time, not silently.
- Keep comment wording in English per this repo's `rules/coding.md` ("Comments and log output — English only").

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to this file:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/workflow/workflow_engine.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/workflow/` | No new errors |
| Tests | `uv run pytest tests/test_workflow_engine.py -v` | All pass, including the pre-existing `test_rejected_task_halts` (confirms the comment addition introduced no behavior change) |
| Regression | `uv run pytest tests/ -k "approval or workflow" -q` | No new failures |
| Manual grep | `grep -n "get_pending_approval" scripts/agent/workflow/workflow_engine.py` | No matches remain |
