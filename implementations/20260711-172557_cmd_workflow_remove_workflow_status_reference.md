# Implementation: `cmd_workflow.py` — Remove Broken `/workflow status` Reference

## Goal

Remove the two `"Use '/workflow status' to list pending approval IDs."` lines from `scripts/agent/commands/cmd_workflow.py`'s `_cmd_approve`/`_cmd_reject` validation-error messages, since `/workflow status` is not a registered command anywhere in `command_defs_list.py` (confirmed by grep — only `/approve`/`/reject` are registered under the workflow mixin). Also fix the module's top-of-file summary docstring to match the actual, already-correct in-code error message format.

## Scope

**In scope:**
- `scripts/agent/commands/cmd_workflow.py`:
  - `_cmd_approve`'s validation-error message (~line 93): remove the second line referencing `/workflow status`.
  - `_cmd_reject`'s validation-error message (~line 142): remove the second line referencing `/workflow status`.
  - Module docstring (lines 5-6): update the `_cmd_approve`/`_cmd_reject` one-line summaries to show `<approval_id>` consistently with the actual error-message syntax (`/approve <approval_id> [reason]` / `/reject <approval_id> [reason]`), replacing the current `[approval_id]` (optional-looking) bracket notation.

**Out of scope:**
- Implementing a `/workflow status` command (Option A) — explicitly rejected in the plan's Out-of-Scope section; no new query function, handler, or `CommandDef` registration is added.
- `command_defs_list.py`'s help text (separate implementation doc).
- Any change to `_parse_approval_arg`, `count_pending_approvals`, `find_approval_by_id`, or `resolve_approval`.

## Assumptions

- Both `"Use '/workflow status' to list pending approval IDs."` lines are confirmed present at lines 93 and 142 (direct read), each immediately following `"Approval ID required. Use: /approve <approval_id> [reason]"` / `"...​/reject <approval_id> [reason]"`.
- The surrounding `"Approval ID required. Use: /approve <approval_id> [reason]"` / `"...​/reject <approval_id> [reason]"` line is already correct and must be preserved unchanged.
- The module docstring currently reads:
  ```
  _cmd_approve  — /approve [approval_id] [reason]  Approve a suspended workflow task
  _cmd_reject   — /reject [approval_id] [reason]   Reject a suspended workflow task
  ```
  and should become `<approval_id>` (required, matching the runtime validation which rejects a missing ID) rather than `[approval_id]` (which reads as optional).

## Implementation

### Target file

`scripts/agent/commands/cmd_workflow.py`

### Procedure

1. In `_cmd_approve`'s validation-error branch (~line 91-94), change:
   ```python
   self._out.write_validation_error(
       "Approval ID required. Use: /approve <approval_id> [reason]\n"
       "Use '/workflow status' to list pending approval IDs."
   )
   ```
   to:
   ```python
   self._out.write_validation_error(
       "Approval ID required. Use: /approve <approval_id> [reason]"
   )
   ```
2. In `_cmd_reject`'s validation-error branch (~line 140-143), apply the same removal, substituting `/reject` for `/approve`.
3. In the module docstring (lines 5-6), change `[approval_id]` to `<approval_id>` in both the `_cmd_approve` and `_cmd_reject` summary lines.

### Method

Direct string/line removal at 2 sites plus a docstring text edit; no control-flow, import, or function-signature change.

### Details

- Confirm no other code path (tests, other commands) references `/workflow status` before removing — a repo-wide grep should return no hits outside this file and the docs targeted in the doc-fix implementation docs.
- Keep the remaining single-line error message string under 120 chars.
- Do not touch the `"No pending approval."` or `"Approval {explicit_id!r} not found or not pending."` messages — unrelated to this fix.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to `cmd_workflow.py`:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/commands/cmd_workflow.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/commands/cmd_workflow.py` | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Regression | `uv run pytest tests/ -k "workflow and (approve or reject or approval)" -q` | No new failures |
| Manual grep | `grep -rn "workflow status" scripts/agent/commands/cmd_workflow.py` | No matches remain |
