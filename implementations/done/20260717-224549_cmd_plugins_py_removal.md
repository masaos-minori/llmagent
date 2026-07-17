# Implementation: scripts/agent/commands/cmd_plugins.py (delete)

Source plan: `plans/done/20260717-123416_plan.md` (Implementation step 2)

Gap-filling note: matches the granularity of the 4 existing sibling docs for
this plan step. **Must run AFTER** `registry_py_plugin_removal.md` and
`command_defs_list_py_plugin_removal.md` (both step 1) land — those remove
`cmd_plugins.py`'s sole consumer (`_PluginsMixin` in `CommandRegistry`'s base
list) and the `/plugin` `CommandDef` entry that routes to `_cmd_plugin`.

## Goal

`scripts/agent/commands/cmd_plugins.py` no longer exists; `_PluginsMixin` and
`_cmd_plugin` are gone from the codebase.

## Scope

**In scope**: delete `scripts/agent/commands/cmd_plugins.py` (37 lines) in full.

**Out of scope**: `registry.py`'s base-class list and `command_defs_list.py`'s
`_COMMANDS` entry (already edited by the step-1 docs).

## Assumptions

1. Confirmed by direct read (2026-07-17): this file defines only `_PluginsMixin`
   (subclass of `MixinBase`) with one method, `_cmd_plugin()`, which does a
   function-local `from shared.plugin_registry import get_last_load_result`
   import (line 19) and reads `result.loaded_count`/`.failed`/
   `.tool_conflicts_shadowed`/`.tool_conflicts_allowed`/`.command_shadows_rejected`
   (fields on the `PluginLoadResult` dataclass from `plugin_result.py`,
   already deleted per `implementations/done/`).
2. Confirmed via `grep -rln "cmd_plugins\|_PluginsMixin" scripts/ --include="*.py"` (excluding this file itself): the only hit is `scripts/agent/commands/registry.py`, whose `_PluginsMixin` import and base-class inclusion are removed by `registry_py_plugin_removal.md` (step 1).
3. `MixinBase` (this file's only non-plugin import, from `agent.commands.mixin_base`) has other subclasses across the `cmd_*.py` sibling files and is unaffected by this deletion.

## Implementation

### Target file

`scripts/agent/commands/cmd_plugins.py` (delete)

### Procedure

1. Confirm (re-verify at implementation time) both `registry_py_plugin_removal.md` and `command_defs_list_py_plugin_removal.md` have already landed — `grep -n "cmd_plugins\|_PluginsMixin" scripts/agent/commands/registry.py` and `grep -n '"/plugin"' scripts/agent/commands/command_defs_list.py` must both return 0 matches before proceeding.
2. Delete `scripts/agent/commands/cmd_plugins.py`.

### Method

Whole-file deletion — no other code change.

### Details

- Test file changes (`tests/test_cmd_plugins.py` deletion) are the existing `plugin_test_files_removal` doc's job — do not delete it from this doc.
- `docs/05_agent_11_01_extension-points-plugin-command.md` (a dedicated doc referencing `_cmd_plugin`) is the existing `plugin_documentation_removal` doc's job.

## Validation plan

| Check | Command | Expected |
|---|---|---|
| File deleted | `ls scripts/agent/commands/cmd_plugins.py` | No such file |
| No remaining imports anywhere | `grep -rn "cmd_plugins\|_PluginsMixin" scripts/` | 0 matches |
| Full suite (run only once all step-1/step-2/step-6 docs have landed) | `uv run pytest -q` | all pass, no `ModuleNotFoundError` |
