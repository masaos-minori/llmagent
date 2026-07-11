# Implementation: `startup.py` Pending-Approval Recovery Fix

## Goal

Fix two bugs in `scripts/agent/startup.py::_recover_pending_approvals()`:
1. The recovery warning message tells the user to run `/approve [reason]` or `/reject [reason]`, omitting the required `approval_id` argument. Following this message verbatim triggers the command handler's "Approval ID required" validation error every time.
2. `ctx.turn.pending_approval_task_id` is never set during recovery, even though the dataclass field exists (`scripts/agent/context.py:81`) and is relied upon elsewhere (`orchestrator.py:184-187`, `cmd_workflow.py:120`) to resume the workflow after approval.

## Scope

**In scope:**
- `scripts/agent/startup.py`, function `_recover_pending_approvals()` (current warning at line ~317; assignment block at lines ~305-309).

**Out of scope:**
- Any other function in `startup.py`.
- The `orchestrator.py` warning fixes (separate implementation doc).
- Any change to `find_latest_pending_approval` or `StateStore`.

## Assumptions

- `approval.approval_id` and `task_id` are both already in local scope at the warning call site (confirmed by direct read of `startup.py:293-318`).
- `ctx.turn.pending_approval_task_id: str | None = None` already exists as a dataclass field on the turn-state object (confirmed at `scripts/agent/context.py:81`) — no new field needs to be added, only the missing assignment.
- No other caller depends on `pending_approval_task_id` staying `None` after recovery.

## Implementation

### Target file

`scripts/agent/startup.py`

### Procedure

1. Open `_recover_pending_approvals()` in `scripts/agent/startup.py`.
2. Immediately after the existing line `ctx.turn.pending_approval_id = approval.approval_id`, add:
   ```python
   ctx.turn.pending_approval_task_id = task_id
   ```
3. Update the `self._view.write_warning(...)` call (currently ending with `f"Use /approve [reason] or /reject [reason]."`) to interpolate the real `approval_id`:
   ```python
   f"Use /approve {approval.approval_id} [reason] or /reject {approval.approval_id} [reason]."
   ```
4. Leave the `logger.warning(...)` call above it unchanged (it already logs `task_id`/`approval_id`/`reason` as structured fields, not as user-facing command syntax).

### Method

Direct in-place edit of the existing function body; no new function, parameter, or import required.

### Details

- Diff is confined to two lines: one new assignment statement, one string-interpolation change.
- No behavior change to the `approval_pending` flag or the `find_latest_pending_approval` lookup.
- Line length must stay within 120 chars (`rules/coding.md`); wrap the f-string across existing line continuations as already done in the surrounding code.
- Do not add a `# noqa`/`# type: ignore` — none should be needed for this change.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to `startup.py`:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/startup.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/startup.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Tests | `uv run pytest tests/test_startup.py tests/test_startup_validation_pipeline.py -k "approval or recover" -v` | All pass, including a new/updated test asserting both `ctx.turn.pending_approval_id` and `ctx.turn.pending_approval_task_id` are restored after recovery |
| Manual grep | `grep -rn "/approve \[reason\]\|/reject \[reason\]" scripts/agent/startup.py` | No matches remain |
