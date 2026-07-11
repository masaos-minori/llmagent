# Implementation Procedure: approval_ops.py — rename `get_pending_approval()` → `get_latest_approval()`

Source plan: `plans/20260711-173259_plan.md` — Design §1 / Implementation step 1

## Goal

Fix the misleading name of `approval_ops.get_pending_approval()`, which actually returns the *latest* approval record for a task regardless of status (no `status='pending'` filter exists in its query) — rename it to `get_latest_approval()` to match its real, load-bearing behavior.

## Scope

**In:**
- `scripts/agent/workflow/approval_ops.py`: rename the function and rewrite its docstring to state the true behavior explicitly and point callers needing status-scoped lookups to the correct alternatives.

**Out:**
- No change to the function body/query itself (`SELECT * FROM approvals WHERE task_id=? ORDER BY created_at DESC LIMIT 1`) — only the name and docstring change.
- No backward-compatible alias — consistent with this session's established convention of not adding compat shims for an internal, single-production-caller function with no external/plugin consumers.

## Assumptions

1. Confirmed by direct read of `approval_ops.py:52-70`: the query has no `WHERE status='pending'` clause. Its sole production caller, `WorkflowEngine._gate_approval()` (`workflow_engine.py:143`), depends on this exact behavior — it fetches the row and branches on `existing.status` being `"approved"`, `"pending"`, or `"rejected"`, which would be impossible if the function only ever returned pending rows.
2. `grep -rn "get_pending_approval"` confirms exactly 9 references: 1 production call site (`workflow_engine.py:143`, plus its import) and 8 test references across `tests/test_workflow_state_store.py`, `tests/test_approval_ops.py`, `tests/test_workflow_engine.py` — all plain Python imports/calls, no dynamic dispatch or string-based lookup.

## Implementation

### Target file

`scripts/agent/workflow/approval_ops.py`

### Procedure

1. Locate `def get_pending_approval(db: SQLiteHelper, task_id: str) -> ApprovalRecord | None:`.
2. Rename the function to `get_latest_approval`, keeping its signature and body unchanged.
3. Replace its docstring with:
   ```python
   """Return the most recent approval record for a task, regardless of status.

   Not filtered to status='pending' — callers that need only pending records
   should filter on the returned record's `.status`, or use
   `find_pending_approval_by_session()` / `find_latest_pending_approval()` /
   `find_approval_by_id()` for status-scoped lookups.
   """
   ```
4. Do not add a `get_pending_approval = get_latest_approval` alias — no backward-compat shim (Assumption above).

### Method

Simple `def` rename plus docstring rewrite. No signature, return-type, or query-logic change. This is a mechanical, fully-enumerable rename (single production caller confirmed via grep).

### Details

- After renaming here, the caller update (`workflow_engine.py`) and test-file updates are handled by companion docs — do not update those files as part of this item; only `approval_ops.py` itself.
- Re-run `grep -n "get_pending_approval" scripts/agent/workflow/approval_ops.py` after the edit to confirm zero remaining occurrences in this file.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to this file:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/workflow/approval_ops.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/workflow/` | No new errors |
| Tests | `uv run pytest tests/test_approval_ops.py -v` | All pass once companion test-file updates land |
| Manual grep | `grep -rn "get_pending_approval" scripts/ tests/ docs/` | No matches remain anywhere (verified after all companion docs are also implemented) |
