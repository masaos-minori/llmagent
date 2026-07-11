# Implementation: `command_defs_list.py` — Fix `/approve`/`/reject` Help Text

## Goal

Fix the `/approve` and `/reject` `CommandDef` help-text strings in `scripts/agent/commands/command_defs_list.py` so they mention the required `approval_id` argument, matching the actual handler behavior (`cmd_workflow.py::_cmd_approve`/`_cmd_reject` unconditionally require it).

## Scope

**In scope:**
- `scripts/agent/commands/command_defs_list.py`: the two `CommandDef(...)` entries for `/approve` and `/reject` (~lines 154-167).

**Out of scope:**
- Any other `CommandDef` entry in this file.
- The actual command handlers in `cmd_workflow.py` (separate implementation doc).

## Assumptions

- Current help text (confirmed by direct read):
  ```python
  CommandDef("/approve", True, False, "_cmd_approve", "[reason]  Approve the pending workflow task"),
  CommandDef("/reject", True, False, "_cmd_reject", "[reason]  Reject the pending workflow task"),
  ```
  omits `approval_id` entirely, understating the actual required argument.
- `CommandDef`'s constructor signature/positional-argument order is unchanged by this fix — only the trailing help-text string literal is edited.

## Implementation

### Target file

`scripts/agent/commands/command_defs_list.py`

### Procedure

1. Locate the `/approve` `CommandDef` entry (~line 154-160).
2. Replace its help-text argument:
   ```python
   "[reason]  Approve the pending workflow task"
   ```
   with:
   ```python
   "<approval_id> [reason]  Approve the pending workflow task"
   ```
3. Locate the `/reject` `CommandDef` entry (~line 161-167) and apply the equivalent replacement:
   ```python
   "<approval_id> [reason]  Reject the pending workflow task"
   ```
4. Leave all other positional arguments (`name`, boolean flags, handler name) unchanged.

### Method

Direct string-literal edit at 2 sites; no structural change to `CommandDef` or the surrounding list.

### Details

- Keep each edited line under 120 chars.
- Confirm no other place in the codebase renders this help text with an assumption that `approval_id` is absent (e.g. a `/help` formatter that pads/aligns columns) — if such a formatter exists, verify the new, longer string does not break alignment; fix formatting only if actually broken.

## Validation plan

Filtered from the plan's Validation plan table to checks relevant to `command_defs_list.py`:

| Check | Tool | Target |
|---|---|---|
| Lint | `uv run ruff check scripts/agent/commands/command_defs_list.py` | 0 errors |
| Type check | `uv run mypy scripts/agent/commands/cmd_workflow.py` (per plan's targeted type-check list; command_defs_list.py covered by `uv run mypy scripts/` full run) | No new errors |
| Architecture | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Regression | `uv run pytest tests/ -k "workflow and (approve or reject or approval)" -q` | No new failures |
| Manual grep | `grep -rn "\"\[reason\]  Approve\|\"\[reason\]  Reject" scripts/agent/commands/command_defs_list.py` | No matches remain |
