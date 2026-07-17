# Implementation: delete `scripts/shared/plugin_conflicts.py`

Source plan: `plans/20260717-123416_plan.md` ("Remove plugin subsystem completely"), Implementation
step 2, per plan Assumption 6.

## Goal

Delete `scripts/shared/plugin_conflicts.py` (95 lines, `validate_command_conflicts`/
`validate_tool_conflicts`) — a file the requirement's own target-file list omits, but which the plan
explicitly flags (Assumption 6) as part of the same subsystem and required to avoid a dangling import
in `plugin_auto_discover.py`.

## Scope

**In scope**
- Delete the file `scripts/shared/plugin_conflicts.py` in full.
- Confirm it has exactly one caller (`plugin_auto_discover.py`, imported at line 10, called at
  lines 78-81) and that caller is deleted in the same batch (sibling item in this batch).

**Out of scope**
- Any replacement conflict-detection mechanism between MCP tool names and registry entries (belongs to
  `RuntimeToolRegistry` work, requirement 02, if needed at all).

## Assumptions

1. Per plan Assumption 6: this file is a direct dependency of `plugin_auto_discover.py` (imported at
   line 10, called at lines 78-81) and has no other purpose — confirmed by direct read of both files
   during this implementation-doc's investigation (`plugin_conflicts.py`'s only import of
   `plugin_registries` is `TYPE_CHECKING`-only at module scope, with two runtime imports inside the
   functions themselves at lines 28 and 71 to break a circular import with `plugin_registries.py`).
2. No file outside the plugin subsystem imports `validate_command_conflicts` or
   `validate_tool_conflicts` — confirmed via `rg -n "plugin_conflicts\|validate_command_conflicts\|validate_tool_conflicts" scripts/`
   returning only `plugin_auto_discover.py` (the sibling deletion item) and this file itself.

## Implementation

### Target file

`scripts/shared/plugin_conflicts.py` (95 lines) — delete in full.

### Procedure

1. Verify via `rg -n "plugin_conflicts\|validate_command_conflicts\|validate_tool_conflicts" scripts/`
   that the only reference is the `plugin_auto_discover.py` import/call site (sibling item in this
   batch, itself scheduled for deletion).
2. Delete the file: `git rm scripts/shared/plugin_conflicts.py`.
3. Re-run the same grep against `scripts/ tests/ docs/` to confirm zero remaining references outside
   this plan's own commit history.

### Method

Pure file deletion — no code transformation needed. Note the deletion ordering constraint from the
plan's Design section: `plugin_auto_discover.py` (the caller) and `plugin_conflicts.py` (the callee)
should land in the same commit (or callee-after-caller) so the tree never has a transient state where
`plugin_auto_discover.py` still imports a now-deleted `plugin_conflicts`.

### Details

- Current content: `validate_tool_conflicts(known_tools, override_policy, strict_mode=False) ->
  tuple[int, int, list[str]]` (shadowed_count, allowed_count, strict_rejected_names) and
  `validate_command_conflicts(strict_mode=False) -> tuple[int, list[str]]` (shadowed_count,
  strict_rejected_names). Both mutate the shared `_tools`/`_commands` dicts from
  `plugin_registries.py` (imported locally inside each function, lines 28 and 71, to avoid a circular
  import at module scope — the module-scope import at lines 9-14 is `TYPE_CHECKING`-only).
- No production logic outside the plugin subsystem depends on these two functions' return shape or
  side effects.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| No remaining references | `rg -n "plugin_conflicts\|validate_command_conflicts\|validate_tool_conflicts" scripts/ tests/ docs/` | 0 matches |
| Import health | `PYTHONPATH=scripts uv run lint-imports` | 0 violations |
| Lint | `uv run ruff check scripts/` | 0 errors |
| Type check | `uv run mypy scripts/` | no new errors |
| Full suite | `uv run pytest -v` | all pass |
