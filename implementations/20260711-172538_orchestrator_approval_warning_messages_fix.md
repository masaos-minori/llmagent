# Implementation: `orchestrator.py` Approval Warning Message Fix

## Goal

Fix 3 runtime warning messages in `scripts/agent/orchestrator.py` that instruct the user to run `/approve [reason]` or `/reject [reason]`, omitting the required `approval_id` argument. This causes the actual command handler (`cmd_workflow.py::_cmd_approve`/`_cmd_reject`) to reject the command with "Approval ID required" every time a user follows the message verbatim.

## Scope

**In scope:**
- `scripts/agent/orchestrator.py`: 3 warning-message sites (current line numbers ~152, ~157, ~306):
  1. `logger.warning("Turn blocked: workflow pending approval. Use /approve or /reject.")` (~line 152)
  2. The `RuntimeError` message passed to `self._on_error`: `"[workflow] Approval is pending — use /approve [reason] or /reject [reason]."` (~line 157)
  3. `logger.warning("[workflow] Approval required. Use /approve [reason] or /reject [reason].")` (~line 306)

**Out of scope:**
- `startup.py`'s recovery warning (separate implementation doc).
- Any other logic in `handle_turn` or the workflow-halt handler.

## Assumptions

- Each of the 3 sites already has the relevant `approval_id` value available in local scope, confirmed by direct read:
  - Site 1/2 (`handle_turn` guard): `ctx.workflow.approval_pending` is checked; `ctx.turn.pending_approval_id` holds the pending approval's ID at this point.
  - Site 3 (approval-required handler): `exc.approval_id` is available from the `WorkflowPendingApprovalError` exception object (already used a few lines above to set `ctx.turn.pending_approval_id = exc.approval_id`).
- No behavioral change is needed beyond the message text — the guard/blocking logic itself is correct and out of scope.

## Implementation

### Target file

`scripts/agent/orchestrator.py`

### Procedure

1. At the `handle_turn` guard (~line 152), change:
   ```python
   logger.warning(
       "Turn blocked: workflow pending approval. Use /approve or /reject."
   )
   ```
   to interpolate `ctx.turn.pending_approval_id`, e.g.:
   ```python
   logger.warning(
       "Turn blocked: workflow pending approval. Use /approve %s or /reject %s.",
       ctx.turn.pending_approval_id,
       ctx.turn.pending_approval_id,
   )
   ```
2. At the same guard's `RuntimeError` (~line 157), change:
   ```python
   "[workflow] Approval is pending — use /approve [reason] or /reject [reason]."
   ```
   to:
   ```python
   f"[workflow] Approval is pending — use /approve {ctx.turn.pending_approval_id} [reason] "
   f"or /reject {ctx.turn.pending_approval_id} [reason]."
   ```
3. At the approval-required handler (~line 306), change:
   ```python
   logger.warning(
       "[workflow] Approval required. Use /approve [reason] or /reject [reason]."
   )
   ```
   to:
   ```python
   logger.warning(
       "[workflow] Approval required. Use /approve %s [reason] or /reject %s [reason].",
       exc.approval_id,
       exc.approval_id,
   )
   ```

### Method

Direct in-place string/format edits at each of the 3 sites; no new function, parameter, or import required. Use `%s` lazy logging formatting for `logger.warning` calls (consistent with existing style in this file) and f-strings only for the exception message per `rules/coding.md`.

### Details

- Verify at implementation time (before each edit) that the variable holding the approval ID is exactly `ctx.turn.pending_approval_id` (sites 1/2) vs `exc.approval_id` (site 3) — do not assume identical variable names across sites.
- Keep each line under 120 chars.
- No change to control flow, only to message content/formatting.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to `orchestrator.py`:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/orchestrator.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/orchestrator.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Regression | `uv run pytest tests/ -k "workflow and (approve or reject or approval)" -q` | No new failures |
| Manual grep | `grep -rn "/approve \[reason\]\|/reject \[reason\]\|Use /approve or /reject" scripts/agent/orchestrator.py` | No matches remain |
